# TOEIC Coach Admin System

A comprehensive admin panel for the TOEIC Coach platform with Role-Based Access Control (RBAC), organization management, audit logging, and advanced reporting capabilities.

## 🚀 Features

### Core Admin Features
- **RBAC System**: 5 predefined roles (Super Admin, Exam Admin, Proctor, Content Editor, Viewer)
- **Organization Hierarchy**: Year → Program → Group structure
- **User Management**: CRUD operations, role assignment, status management
- **Question Bank**: Manage questions, bulk import/export
- **Audit Logging**: Complete activity tracking
- **Reports & Analytics**: Performance dashboards and KPIs
- **Import/Export**: CSV/XLSX support for data management

### Security & Compliance
- **Permission-based Access Control**: Granular permissions for all operations
- **Audit Trail**: Complete logging of all admin actions
- **Session Management**: Secure admin sessions
- **Data Privacy**: PII masking capabilities

## 📋 Admin Roles

| Role | Permissions | Description |
|------|-------------|-------------|
| **Super Admin** | All permissions | Full system access, user management, system configuration |
| **Exam Admin** | Exam & session management | Manage exams, sessions, view reports |
| **Proctor/Instructor** | Session monitoring | Monitor exam sessions, view student progress |
| **Content Editor** | Question management | Manage question bank, create/edit questions |
| **Viewer** | Read-only access | View reports and basic data |

## 🏗️ System Architecture

### Database Models
- **User**: Enhanced with RBAC fields (first_name, last_name, phone, is_active, etc.)
- **Role**: Permission-based roles with JSON permission storage
- **UserRole**: Many-to-many user-role relationships
- **Year/Program/Group**: Organization hierarchy
- **AuditLog**: Complete audit trail
- **NotificationTemplate/Notification**: Email/SMS system

### Admin Routes (`/admin`)
- `/` - Dashboard with statistics and quick actions
- `/users` - User management with search/filters
- `/users/create` - Create new users
- `/users/<id>/edit` - Edit user details
- `/questions` - Question bank management
- `/organizations` - Organization hierarchy
- `/audit-logs` - Activity logs
- `/reports` - Analytics dashboard
- `/import-export` - Data management

## 🛠️ Installation & Setup

### 1. Initialize Admin System
```bash
# Run the initialization script
python init_admin.py
```

This will:
- Create all database tables
- Set up RBAC roles and permissions
- Create organization hierarchy
- Create admin user

### 2. Default Admin Credentials
```
Username: admin
Email: admin@toeic.com
Password: admin123
Role: Super Administrator
```

### 3. Access Admin Panel
Navigate to: `http://localhost:5050/admin`

## 📊 Admin Dashboard

The dashboard provides:
- **Statistics Cards**: Total users, questions, exams, roles
- **Quick Actions**: Create user, add question, new academic year
- **Recent Activity**: Latest users and audit logs
- **System Status**: Database, file system, notifications, security

## 👥 User Management

### Features
- **Search & Filter**: By username, email, role, status
- **Bulk Operations**: Export users to CSV
- **Role Assignment**: Multiple roles per user
- **Status Management**: Active/inactive users
- **Audit Trail**: Track all user modifications

### User Creation
- Required fields: Username, Email, Password
- Optional fields: First Name, Last Name, Phone
- Role assignment with descriptions
- Active/inactive status toggle

## 🏫 Organization Management

### Hierarchy Structure
```
Academic Year (2024-2025)
├── Program (Computer Science)
│   ├── Group A
│   └── Group B
├── Program (Business Administration)
│   ├── Group A
│   └── Group B
└── Program (English Language)
    └── Group A
```

### Management Features
- Create academic years with date ranges
- Add programs within years
- Create student groups
- Assign users to groups
- Track group membership history

## 📝 Question Bank Management

### Features
- **Search & Filter**: By part, test set, question text
- **Bulk Import**: CSV/XLSX support
- **Question Details**: Full question view with options
- **Test Set Management**: Organize by test versions
- **Audit Logging**: Track all question modifications

## 📈 Reports & Analytics

### Available Reports
- **User Performance**: Average scores, attempt counts, best scores
- **System Statistics**: User counts, question counts, exam statistics
- **Activity Reports**: Recent exam attempts, user activity
- **Audit Reports**: Admin actions, system changes

### Export Capabilities
- **CSV Export**: Users, questions, audit logs
- **Filtered Exports**: Based on search criteria
- **Bulk Operations**: Mass data operations

## 🔍 Audit Logging

### Tracked Actions
- User creation, updates, deletions
- Role assignments and changes
- Question modifications
- Organization changes
- System configuration changes
- Data imports/exports

### Audit Log Details
- User who performed action
- Action type and resource
- Old and new values
- IP address and user agent
- Timestamp

## 🔐 Security Features

### Access Control
- **Permission-based**: Granular permission system
- **Role Hierarchy**: Inherited permissions
- **Session Security**: Secure admin sessions
- **IP Tracking**: Audit log IP addresses

### Data Protection
- **PII Masking**: Personal information protection
- **Audit Trail**: Complete activity logging
- **Secure Storage**: Encrypted sensitive data

## 🚀 Advanced Features

### Import/Export System
- **CSV Support**: Users, questions, audit logs
- **XLSX Support**: Complex data structures
- **Validation**: Data integrity checks
- **Templates**: Predefined import formats

### Notification System
- **Email Templates**: Customizable email notifications
- **SMS Support**: Text message notifications
- **Template Variables**: Dynamic content
- **Delivery Tracking**: Status monitoring

## 🔧 Configuration

### Environment Variables
```bash
# Database
SQLALCHEMY_DATABASE_URI=sqlite:///toeic.db

# Security
SECRET_KEY=your-secret-key

# Admin Settings
ADMIN_EMAIL=admin@toeic.com
ADMIN_PASSWORD=admin123
```

### Customization
- **Roles**: Add custom roles in `init_rbac_data()`
- **Permissions**: Define new permissions
- **Organization**: Modify hierarchy structure
- **Templates**: Customize admin UI

## 📱 Responsive Design

The admin panel is fully responsive with:
- **Mobile-first**: Optimized for mobile devices
- **Bootstrap 5**: Modern UI framework
- **Font Awesome**: Professional icons
- **Custom CSS**: Branded styling

## 🧪 Testing

### Test Admin Access
1. Login with admin credentials
2. Navigate to `/admin`
3. Test user creation
4. Verify role assignments
5. Check audit logs

### Test Permissions
1. Create test users with different roles
2. Verify permission restrictions
3. Test role-based UI elements
4. Validate audit logging

## 🚨 Troubleshooting

### Common Issues

**Admin Panel Not Accessible**
- Check if admin blueprint is registered
- Verify database tables exist
- Check user permissions

**Permission Errors**
- Verify role assignments
- Check permission definitions
- Review audit logs

**Database Issues**
- Run migration script: `python migrate_user_table.py`
- Reinitialize: `python init_admin.py`
- Check database connection

## 📚 API Documentation

### Admin Endpoints
- `GET /admin/` - Dashboard
- `GET /admin/users` - User list
- `POST /admin/users/create` - Create user
- `GET /admin/users/<id>` - User details
- `POST /admin/users/<id>/edit` - Update user
- `GET /admin/export/users` - Export users
- `GET /admin/audit-logs` - Audit logs

### Permission Checks
All admin routes include permission decorators:
- `@require_permission('permission.name')`
- `@admin_required` (for super admin only)

## 🔄 Migration Guide

### From Basic TOEIC Coach
1. Run `python migrate_user_table.py`
2. Run `python init_admin.py`
3. Update `app.py` to include admin blueprint
4. Test admin functionality

### Database Schema Changes
- Added RBAC tables (Role, UserRole)
- Added organization tables (Year, Program, Group)
- Added audit tables (AuditLog)
- Added notification tables (NotificationTemplate, Notification)
- Enhanced User table with RBAC fields

## 🎯 Future Enhancements

### Planned Features
- **SSO Integration**: Single Sign-On support
- **Advanced Analytics**: Machine learning insights
- **API Rate Limiting**: Request throttling
- **Real-time Notifications**: WebSocket support
- **Advanced Reporting**: Custom report builder
- **Bulk Operations**: Mass user/role management

### Extensibility
- **Plugin System**: Custom admin modules
- **Theme Support**: Customizable UI themes
- **API Extensions**: RESTful admin API
- **Webhook Support**: External integrations

## 📞 Support

For admin system support:
1. Check audit logs for errors
2. Review permission assignments
3. Verify database integrity
4. Test with different user roles

## 📄 License

This admin system is part of the TOEIC Coach platform and follows the same licensing terms.
