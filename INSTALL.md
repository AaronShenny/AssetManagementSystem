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



