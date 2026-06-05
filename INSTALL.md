# PostgreSQL Setup for Frappe

## Install PostgreSQL

```bash
brew update
brew install postgresql@16
```

Verify installation:

```bash
psql --version
```

## Start PostgreSQL

```bash
brew services start postgresql@16
```

## Create a PostgreSQL User

```bash
psql postgres
```

```sql
CREATE USER frappe WITH PASSWORD 'your_password';
ALTER USER frappe CREATEDB;
\q
```

## Create a New Frappe Site Using PostgreSQL

```bash
bench new-site byt.local --db-type postgres
```

Provide the requested PostgreSQL credentials when prompted:

* Host: `localhost`
* Port: `5432`
* User: `frappe`
* Password: `<your_password>`

## Install the Application

```bash
bench get-app https://github.com/AaronShenny/AssetManagementSystem.git
bench --site byt.local install-app asset_system
```

## Run Migrations

```bash
bench --site byt.local migrate
```

## Start the Development Server

```bash
bench start
```

The site will be available at:

```text
http://localhost:8000
```

# Role Permission Manager
## Infra Admin
<img width="1920" height="968" alt="image" src="https://github.com/user-attachments/assets/d7a19947-90ba-43ea-9b04-3eb3d4bb697c" />
<img width="1920" height="966" alt="image" src="https://github.com/user-attachments/assets/20e12fc2-4148-4560-9868-b2e34b1b47d9" />

## Infra Executive
<img width="1925" height="967" alt="image" src="https://github.com/user-attachments/assets/56ad46f1-47d8-4cd4-b4c9-e05b8d2792cf" />
<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/f02673f5-92c8-4d6b-bfec-32b38a5583b5" />

## Leadership
<img width="1918" height="959" alt="image" src="https://github.com/user-attachments/assets/097bc6bd-0779-4213-8ed4-e339de7a09af" />
<img width="1919" height="968" alt="image" src="https://github.com/user-attachments/assets/3bb9e62f-508a-4a3a-9352-118feff5c2ee" />

## Employee
<img width="1919" height="960" alt="image" src="https://github.com/user-attachments/assets/b30e532d-32e2-4b86-ace6-a6a579800a3e" />



# Clone Frontend Repository

```bash
git clone https://github.com/AaronShenny/ReactERP.git
cd ReactERP
```

## Install Dependencies

```bash
npm install
```

## Configure Environment Variables

Create a `.env` file and configure the backend URL as required.

Example:

```env
VITE_API_URL=http://localhost:8000
```

## Start Development Server

```bash
npm run dev
```

The application will be available at:

```text
http://localhost:5173
```


# AD WORKFLOW2 |Asset Deregistration
<img width="833" height="696" alt="image" src="https://github.com/user-attachments/assets/d4f8f40e-39b0-4613-82f8-aafb52054239" />

# AD WORKFLOW 2 | Asset Issues
<img width="1252" height="948" alt="image" src="https://github.com/user-attachments/assets/26901ee4-a09f-4e43-abb2-70a92da01760" />

## Steps
1. Create [Employee, Infra Admin, Infra Executive, Leadership] Roles in Frappe.
2. Give permissions for each role as per the above images
3. When We create a user, a default employee role would be placed [ user_hooks.py ]
4. Change the login redirect. In the zip file, it would directly goes to frappe's login. But in production, it should directly redirect to microsoft login [ src/pages/login.jsx]
    window.location.href = `https://login.microsoftonline.com/fc44c070-fb0f-4e32-b713-14422945e334/oauth2/v2.0/authorize?redirect_uri=${API_BASE}%2Fapi%2Fmethod%2Ffrappe.integrations.oauth2_logins.login_via_office365&state=eyJzaXRlIjogImh0dHA6Ly9sb2NhbGhvc3Q6ODA4MCIsICJ0b2tlbiI6ICI5MmZhMGEyZjQ1ZTkwNGM0NmY4ZjJlNWMyZTE2MjliZDg1N2RiMTg1MTE2MzhiYjlkMzUzYzc5MyIsICJyZWRpcmVjdF90byI6ICJodHRwOi8vbG9jYWxob3N0OjgwODAvYXBpL21ldGhvZC9mcmFwcGUuaW50ZWdyYXRpb25zLm9hdXRoMi5hdXRob3JpemU%2FY2xpZW50X2lkPXFjcmRzcDg0N20mcmVzcG9uc2VfdHlwZT10b2tlbiZyZWRpcmVjdF91cmk9aHR0cDovL2xvY2FsaG9zdDo1MTczL2F1dGgvY2FsbGJhY2sifQ%3D%3D&response_type=code&scope=openid+profile+email+User.Read&client_id=1624909b-d52e-42c7-a634-b1cd2a426a79`;
5. Change the client secret in React respo and Add oAuth client in frappe
   <img width="1919" height="855" alt="image" src="https://github.com/user-attachments/assets/af654a6d-8ba4-4f3a-97c4-6f71c64df26d" />
6. In social Login key [Custom, dont use office365]
   1. Client id : 1624909b-d52e-42c7-a634-b1cd2a426a79
   2. Client Secret : 
   3. Base URL : https://login.microsoftonline.com
   4. Authorize URL: https://login.microsoftonline.com/fc44c070-fb0f-4e32-b713-14422945e334/oauth2/v2.0/authorize
   5. Redirect URL : /api/method/frappe.integrations.oauth2_logins.login_via_office365
   6. Access Token URL : https://login.microsoftonline.com/fc44c070-fb0f-4e32-b713-14422945e334/oauth2/v2.0/token
   7. Auth URL data :  {"response_type": "code", "scope": "openid profile email User.Read"}
7. After creating social login key [ name : microsoft], go to this \\wsl.localhost\Ubuntu\home\aaron\BYT\frappe-benchv16\apps\frappe\frappe\integrations\oauth2_logins.py 
   Change function login_via_office365():
   @frappe.whitelist(allow_guest=True)
   def login_via_office365(code: str, state: str):
    	login_via_oauth2_id_token("microsoft", code, state, decoder=decoder_compat)
