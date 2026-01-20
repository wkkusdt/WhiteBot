# Render Deployment Guide for WhiteBot

## Environment Variables
Set these in your Render dashboard:

- `BOT_TOKEN` - Your Telegram bot token from @BotFather
- `ADMIN_ID` - Your Telegram user ID (numeric)
- `WEBHOOK_URL` - `https://your-app-name.onrender.com/webhook`
- `PORT` - `8080` (Render automatically sets this)
- `WEBHOOK_PATH` - `/webhook` (optional, defaults to this)

## Deployment Steps

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add webhook support for Render"
   git push origin main
   ```

2. **Create Web Service on Render**:
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `WhiteBot` repo
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Instance Type**: Free (or paid for better performance)

3. **Set Environment Variables**:
   - Add all the variables listed above
   - Make sure `WEBHOOK_URL` uses your actual Render app URL

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Check the logs to ensure webhook is set correctly

## Important Notes

- The bot now automatically detects if it's running in webhook mode (when `WEBHOOK_URL` is set)
- For local development, it will use polling mode (when `WEBHOOK_URL` is not set)
- The webhook server listens on port 8080 and binds to 0.0.0.0 for Render
- SQLite database is stored in `data/submissions.sqlite3`

## Troubleshooting

If deployment fails:
1. Check Render logs for specific error messages
2. Ensure all environment variables are set correctly
3. Verify your bot token is valid
4. Make sure the webhook URL matches your Render app URL

## Webhook Setup

The bot automatically sets the webhook when `WEBHOOK_URL` is provided. You don't need to manually configure it via Telegram API calls.
