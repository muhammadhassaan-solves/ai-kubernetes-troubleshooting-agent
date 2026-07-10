CREATE TABLE IF NOT EXISTS public.investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
  root_cause TEXT NOT NULL,
  namespace TEXT,
  confidence INTEGER NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 100),
  status TEXT NOT NULL DEFAULT 'completed',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS investigations_user_created_idx
  ON public.investigations (user_id, created_at DESC);

DROP POLICY IF EXISTS investigations_select_own ON public.investigations;
CREATE POLICY investigations_select_own
  ON public.investigations
  FOR SELECT TO authenticated
  USING (user_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS investigations_insert_own ON public.investigations;
CREATE POLICY investigations_insert_own
  ON public.investigations
  FOR INSERT TO authenticated
  WITH CHECK (user_id = (SELECT auth.uid()));

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT ON public.investigations TO authenticated;

INSERT INTO realtime.channels (pattern, description, enabled)
VALUES ('investigation:%', 'Per-user Kubernetes investigation progress', true)
ON CONFLICT (pattern) DO UPDATE
SET description = EXCLUDED.description,
    enabled = EXCLUDED.enabled;

ALTER TABLE realtime.channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE realtime.messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS investigations_subscribe_progress ON realtime.channels;
CREATE POLICY investigations_subscribe_progress
  ON realtime.channels
  FOR SELECT TO authenticated
  USING (pattern = 'investigation:%');

DROP POLICY IF EXISTS investigations_publish_progress ON realtime.messages;
CREATE POLICY investigations_publish_progress
  ON realtime.messages
  FOR INSERT TO authenticated
  WITH CHECK (channel_name LIKE 'investigation:%');

