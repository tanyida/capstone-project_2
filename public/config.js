// ParentedSG — connects the site to your Supabase project so parents can sign in and share
// a family account. Leave both values empty to run without accounts (data stays on each device).
//
// Find both on the Supabase dashboard: Project Settings → API.
// The anon key is meant to be public. Row-level security in supabase/schema.sql is what keeps
// each family's records private — run that file before switching accounts on.
window.PARENTEDSG_CONFIG = {
  supabaseUrl: "",      // e.g. "https://abcdefghijklmnop.supabase.co"
  supabaseAnonKey: "",  // the "anon" / "public" key
};
