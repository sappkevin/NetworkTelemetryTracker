
# Google OAuth 2FA Setup for Grafana

This guide provides step-by-step instructions to set up Google OAuth 2.0 authentication for your Grafana dashboard, enabling secure two-factor authentication.

## Prerequisites

- Google account with access to Google Cloud Console
- Running Grafana instance (configured via docker-compose.yml)
- Domain or accessible URL for your Grafana instance

## Step 1: Create Google Cloud Project

1. **Access Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Sign in with your Google account

2. **Create or Select Project**
   - Click on the project dropdown at the top
   - Select "New Project" or choose an existing project
   - Enter project name: `grafana-oauth-project`
   - Click "Create"

## Step 2: Enable Required APIs

1. **Navigate to APIs & Services**
   - In the left sidebar, click "APIs & Services" → "Library"

2. **Enable Google+ API**
   - Search for "Google+ API"
   - Click on it and press "Enable"
   - Wait for activation to complete

3. **Enable OAuth 2.0 API**
   - Search for "Identity and Access Management (IAM) API"
   - Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen

1. **Access OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"

2. **Choose User Type**
   - Select "External" for public access
   - Click "Create"

3. **App Information**
   ```
   App name: Grafana Network Telemetry Dashboard
   User support email: your-email@domain.com
   Developer contact information: your-email@domain.com
   ```

4. **App Domain (Optional)**
   ```
   Application home page: https://your-repl-url.repl.co:3000
   Privacy policy link: https://your-repl-url.repl.co:3000/privacy
   Terms of service link: https://your-repl-url.repl.co:3000/terms
   ```

5. **Authorized Domains**
   - Add your Replit domain: `repl.co`
   - Add localhost for development: `localhost`

6. **Scopes**
   - Click "Add or Remove Scopes"
   - Add these scopes:
     - `userinfo.email`
     - `userinfo.profile`
     - `openid`

7. **Test Users (for Development)**
   - Add your Google email address
   - Add any other test user emails

8. **Save and Continue** through all steps

## Step 4: Create OAuth 2.0 Credentials

1. **Navigate to Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"

2. **Application Type**
   - Select "Web application"

3. **Configure OAuth Client**
   ```
   Name: Grafana OAuth Client
   
   Authorized JavaScript origins:
   - http://localhost:3000
   - https://your-repl-name.your-username.repl.co
   
   Authorized redirect URIs:
   - http://localhost:3000/login/google
   - https://your-repl-name.your-username.repl.co/login/google
   ```

4. **Save Credentials**
   - Click "Create"
   - **Important**: Copy the Client ID and Client Secret immediately
   - Download the JSON file for backup

## Step 5: Configure Environment Variables

1. **Update .env File**
   Add these variables to your `.env` file:

   ```bash
   # Google OAuth Configuration
   GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
   
   # Grafana Security
   GF_SECURITY_ADMIN_PASSWORD=your-secure-admin-password
   GF_SECURITY_SECRET_KEY=your-long-random-secret-key-minimum-32-characters
   ```

2. **Generate Secure Secret Key**
   Use this command to generate a secure secret key:
   ```bash
   openssl rand -base64 32
   ```

## Step 6: Update Grafana Configuration

Your `grafana/grafana.ini` is already configured correctly with these settings:

```ini
[auth.google]
enabled = true
client_id = ${GOOGLE_CLIENT_ID}
client_secret = ${GOOGLE_CLIENT_SECRET}
scopes = https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email
auth_url = https://accounts.google.com/o/oauth2/auth
token_url = https://oauth2.googleapis.com/token
api_url = https://www.googleapis.com/oauth2/v1/userinfo
allow_sign_up = true
role_attribute_path = contains(info.email, '@yourcompany.com') && 'Admin' || 'Editor'
```

## Step 7: Customize User Role Mapping

1. **Edit Role Mapping Rule**
   In `grafana/grafana.ini`, update the `role_attribute_path`:

   ```ini
   # For specific domain admin access:
   role_attribute_path = contains(info.email, '@yourdomain.com') && 'Admin' || 'Editor'
   
   # For specific email admin access:
   role_attribute_path = info.email == 'admin@yourdomain.com' && 'Admin' || 'Editor'
   
   # For all users as editors:
   role_attribute_path = 'Editor'
   ```

## Step 8: Start Services

1. **Start Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Check Service Status**
   ```bash
   docker-compose ps
   ```

3. **View Logs (if needed)**
   ```bash
   docker-compose logs grafana
   ```

## Step 9: Test OAuth Authentication

1. **Access Grafana**
   - Open your browser to `http://localhost:3000` or your Replit URL
   - You should see the Grafana login page

2. **Test Google Login**
   - Click "Sign in with Google"
   - Complete the Google OAuth flow
   - Verify you're redirected back to Grafana

3. **Verify Access**
   - Check that you can access dashboards
   - Verify your user role (Admin/Editor)

## Step 10: Production Deployment

1. **Update Redirect URIs**
   - Add your production domain to Google Cloud Console
   - Update authorized redirect URIs

2. **Publish OAuth App**
   - In Google Cloud Console, go to OAuth consent screen
   - Click "Publish App" to make it available to all users
   - May require verification process

3. **Security Considerations**
   - Use HTTPS in production
   - Set strong admin passwords
   - Regularly rotate OAuth credentials
   - Monitor OAuth usage in Google Cloud Console

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI" Error**
   - Verify redirect URIs in Google Cloud Console exactly match your URLs
   - Check for typos, protocol mismatches (http vs https)

2. **"OAuth flow failed" Error**
   - Ensure Google+ API is enabled
   - Check that OAuth consent screen is properly configured

3. **"Access denied" Error**
   - Verify Client ID and Client Secret in .env file
   - Check that user email is in test users (if app not published)

4. **"User not found" Error**
   - Review role mapping configuration in grafana.ini
   - Check user email domain matches role attribute path

### Debug Commands

```bash
# Check environment variables
docker-compose exec grafana env | grep GOOGLE

# View Grafana logs
docker-compose logs -f grafana

# Test InfluxDB connection
docker-compose exec grafana curl -f http://influxdb2:8086/ping
```

### Security Checklist

- [ ] OAuth client credentials stored securely
- [ ] Strong admin password set
- [ ] Secret key is random and at least 32 characters
- [ ] Test users configured for development
- [ ] Production domains added to authorized URIs
- [ ] OAuth app published for production use

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Grafana OAuth Configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/google/)
- [Google Cloud Console](https://console.cloud.google.com/)

## Support

For issues specific to this setup:
1. Check the troubleshooting section above
2. Review docker-compose logs
3. Verify Google Cloud Console configuration
4. Test with a different Google account
