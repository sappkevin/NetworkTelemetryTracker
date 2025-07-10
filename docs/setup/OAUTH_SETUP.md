# Google OAuth Setup for Grafana

This guide explains how to set up Google OAuth authentication for your Grafana instance.

## Prerequisites

1. A Google Cloud Console project
2. Domain access to configure OAuth settings

## Step 1: Create Google OAuth Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to **APIs & Services** → **Library**
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth 2.0 Client ID**
   - Choose **Web application** as the application type
   - Add authorized redirect URIs:
     - `http://localhost:3000/login/google`
     - `http://your-domain.com:3000/login/google` (if using custom domain)
   - Note down the **Client ID** and **Client Secret**

## Step 2: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here

# Grafana Security
GF_SECURITY_ADMIN_PASSWORD=your-secure-admin-password
GF_SECURITY_SECRET_KEY=your-long-random-secret-key-here
```

## Step 3: Start the Services

```bash
docker-compose up -d
```

## Step 4: Access Grafana

1. Open http://localhost:3000
2. Click "Sign in with Google"
3. Complete the Google OAuth flow
4. You'll be logged in and can access the dashboards

## Security Notes

- Replace default passwords with strong, unique values
- Use HTTPS in production environments
- Configure proper domain restrictions in Google Cloud Console
- Consider using environment-specific OAuth applications (dev/staging/prod)

## Troubleshooting

### Common Issues:

1. **Invalid redirect URI**: Ensure the redirect URI in Google Cloud Console matches exactly
2. **OAuth flow fails**: Check that Google+ API is enabled
3. **Access denied**: Verify the client ID and secret are correct
4. **User not found**: Check the role mapping in grafana.ini

### Role Mapping

By default, users with emails containing '@yourcompany.com' get Admin role, others get Editor role. 
Modify the `role_attribute_path` in `grafana/grafana.ini` to match your organization's email domain.

## Testing

1. Try logging in with different Google accounts
2. Verify role assignments work correctly
3. Test dashboard access permissions
4. Ensure logout works properly