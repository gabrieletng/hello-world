#!/usr/bin/env python3
"""Inject PostHog snippet into every HTML file's <head>.

Edit POSTHOG_KEY below with the project's public key from
https://eu.posthog.com (or us.posthog.com) > Project Settings > Project API Key.
"""
import pathlib
import re
import sys

# Public project key — safe to commit. Host is eu or us depending on region.
POSTHOG_KEY = "phc_REPLACE_ME"
POSTHOG_HOST = "https://eu.i.posthog.com"

SNIPPET = f"""  <!-- PostHog -->
  <script type="text/javascript">
    !function(t,e){{var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){{function g(t,e){{var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){{var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}},u.people.toString=function(){{return u.toString(1)+".people (stub)"}},o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])}},e.__SV=1)}}(document,window.posthog||[]);
    posthog.init('{POSTHOG_KEY}', {{api_host:'{POSTHOG_HOST}', person_profiles:'identified_only', respect_dnt:true}});
  </script>
"""

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD_RE = re.compile(r"(<head\b[^>]*>)", re.IGNORECASE)

def main() -> int:
    files = list(ROOT.rglob("*.html"))
    touched = skipped = missing = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        if "posthog.init(" in text:
            skipped += 1
            continue
        m = HEAD_RE.search(text)
        if not m:
            missing += 1
            print(f"no <head>: {path}", file=sys.stderr)
            continue
        new_text = text[:m.end()] + "\n" + SNIPPET + text[m.end():]
        path.write_text(new_text, encoding="utf-8")
        touched += 1
    print(f"injected: {touched}  skipped: {skipped}  no-head: {missing}  total: {len(files)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
