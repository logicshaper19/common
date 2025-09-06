# Admin Access Guide

Since we removed the demo credentials from the login page for production security, here are the ways to access the admin dashboard:

## Option 1: Automatic Default Admin (Recommended for Development)

The application now automatically creates a default admin user on startup if none exists.

**Default Credentials:**
- **Email:** `elisha@common.co`
- **Password:** `slp225`

These can be customized using environment variables:

```bash
export ADMIN_EMAIL="your-admin@company.com"
export ADMIN_PASSWORD="your-secure-password"
export ADMIN_NAME="Your Name"
export ADMIN_COMPANY_NAME="Your Company"
```

## Option 2: Interactive Admin Creation Script

Run the interactive script to create a custom admin user:

```bash
python create_admin_user.py
```

This script will prompt you for:
- Company name and email
- Admin user name and email  
- Secure password

## Option 3: Environment Variable Script

For automated deployments, use the environment variable script:

```bash
# Set your admin credentials
export ADMIN_EMAIL="admin@yourcompany.com"
export ADMIN_PASSWORD="your-secure-password-here"
export ADMIN_NAME="Your Full Name"
export ADMIN_COMPANY_NAME="Your Company Name"

# Run the script
python app/scripts/create_default_admin.py
```

## Option 4: Manual Database Creation

If you prefer to create the admin user manually in the database:

1. Create a company record in the `companies` table
2. Create a user record in the `users` table with `role = 'admin'`
3. Make sure to hash the password using the same method as the application

## Security Notes

🔒 **For Production:**
- Always change the default password
- Use strong, unique passwords
- Consider using environment variables for credentials
- Enable proper authentication and authorization

🔧 **For Development:**
- The default admin user is created automatically
- You can use the interactive script for custom setups
- Environment variables override defaults

## Accessing the Admin Dashboard

Once you have admin credentials:

1. Start your backend server: `uvicorn app.main:app --reload`
2. Start your frontend: `npm start` (in the frontend directory)
3. Navigate to the login page
4. Use your admin credentials to log in
5. You'll have access to all admin features including:
   - System monitoring
   - User management
   - Product catalog management
   - Company management
   - Audit logs

## Troubleshooting

**If you can't log in:**
1. Check that the backend server is running
2. Verify the database connection
3. Check the application logs for errors
4. Try creating a new admin user with the scripts

**If the admin user doesn't exist:**
1. Run the application once to trigger automatic creation
2. Or use one of the manual creation scripts above
3. Check the database to verify the user was created

**Database Issues:**
1. Ensure your database is running and accessible
2. Check the `DATABASE_URL` environment variable
3. Run database migrations if needed
4. Check file permissions for SQLite databases