# User Guide: Isolated Browser Profile for Auto-Apply

To allow the bot to postulations using your account without manual login:

1. **Create the profile:** Run Chrome once with a custom directory:
   `google-chrome --user-data-dir=$(pwd)/.browser_profiles/bot_profile`
2. **Login:** Manually log in to StepStone, LinkedIn, etc. Solve any Captchas.
3. **Accept Cookies:** Ensure you accept cookies so the session persists.
4. **Close Chrome:** Exit completely.
5. **Run the Bot:** The `PlaywrightFetcher` is configured to use this path. **CRITICAL:** Close your personal Chrome if it uses the same path, or better yet, keep them isolated.
