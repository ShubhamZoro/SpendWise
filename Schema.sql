-- Smart Family Expense Tracker Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create profiles table (extends Supabase Auth users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create groups table
CREATE TABLE IF NOT EXISTS public.groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    invite_code TEXT UNIQUE NOT NULL,
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create group_members junction table
CREATE TABLE IF NOT EXISTS public.group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    role TEXT DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, group_id)
);

-- Create expenses table
CREATE TABLE IF NOT EXISTS public.expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    group_id UUID REFERENCES public.groups(id) ON DELETE CASCADE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount >= 0),
    category TEXT NOT NULL,
    date DATE NOT NULL,
    notes TEXT,
    receipt_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_group_members_user ON public.group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group ON public.group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_expenses_user ON public.expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_group ON public.expenses(group_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON public.expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON public.expenses(category);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Groups policies
CREATE OR REPLACE FUNCTION get_user_groups()
RETURNS SETOF UUID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT group_id FROM group_members WHERE user_id = auth.uid();
$$;

CREATE POLICY "Users can view groups they are members of"
    ON public.groups FOR SELECT
    USING (id IN (SELECT get_user_groups()) OR auth.uid() = created_by);

CREATE POLICY "Users can create groups"
    ON public.groups FOR INSERT
    WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Group owners can update groups"
    ON public.groups FOR UPDATE
    USING (auth.uid() = created_by);

CREATE POLICY "Group owners can delete groups"
    ON public.groups FOR DELETE
    USING (auth.uid() = created_by);

-- Group members policies
CREATE POLICY "Users can view group members of groups they belong to"
    ON public.group_members FOR SELECT
    USING (group_id IN (SELECT get_user_groups()));

CREATE POLICY "Users can join groups"
    ON public.group_members FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can leave groups"
    ON public.group_members FOR DELETE
    USING (auth.uid() = user_id);

-- Expenses policies
CREATE POLICY "Users can view expenses from groups they belong to"
    ON public.expenses FOR SELECT
    USING (group_id IN (SELECT get_user_groups()));

CREATE POLICY "Users can create expenses in groups they belong to"
    ON public.expenses FOR INSERT
    WITH CHECK (
        auth.uid() = user_id AND
        group_id IN (SELECT get_user_groups())
    );

CREATE POLICY "Users can update their own expenses"
    ON public.expenses FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own expenses"
    ON public.expenses FOR DELETE
    USING (auth.uid() = user_id);

-- Function to handle new user signup (auto-create profile)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to generate random invite code
CREATE OR REPLACE FUNCTION public.generate_invite_code()
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    code TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..6 LOOP
        code := code || substr(chars, floor(random() * length(chars) + 1)::integer, 1);
    END LOOP;
    RETURN code;
END;
$$ LANGUAGE plpgsql;

-- Function to get group analytics (for AI insights)
CREATE OR REPLACE FUNCTION public.get_group_analytics(
    p_group_id UUID,
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    total_amount DECIMAL,
    avg_amount DECIMAL,
    expense_count BIGINT,
    category_breakdown JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(e.amount), 0) as total_amount,
        COALESCE(AVG(e.amount), 0) as avg_amount,
        COUNT(e.id)::BIGINT as expense_count,
        jsonb_build_object(
            'categories', (
                SELECT jsonb_object_agg(category, category_total)
                FROM (
                    SELECT category, SUM(amount) as category_total
                    FROM expenses
                    WHERE group_id = p_group_id 
                        AND date >= p_start_date 
                        AND date <= p_end_date
                    GROUP BY category
                ) cat_totals
            )
        ) as category_breakdown
    FROM expenses e
    WHERE e.group_id = p_group_id 
        AND e.date >= p_start_date 
        AND e.date <= p_end_date;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
