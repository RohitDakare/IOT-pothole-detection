# Deploying Pothole Detection System to Google Cloud (GCP)

This guide will walk you through deploying your backend server on a Google Cloud Platform (GCP) Compute Engine instance.

## Prerequisites
- A Google Cloud Account
- Compute Engine API enabled
- Basic familiarity with terminal commands

---

## Step 1: Create a VM Instance
1. Go to **Compute Engine > VM Instances**.
2. Click **Create Instance**.
3. **Region**: Choose one close to you (e.g., `asia-south1` for Mumbai).
4. **Machine Type**: `e2-micro` (Free tier eligible) or `e2-small` is sufficient.
5. **Boot Disk**: Select **Ubuntu 22.04 LTS** (Recommended).
6. **Firewall**: Check both **Allow HTTP traffic** and **Allow HTTPS traffic**.
7. Click **Create**.

## Step 2: Configure Firewall Rules (Important!)
By default, GCP blocks port 8000. You must open it.
1. Go to **VPC Network > Firewall**.
2. Click **Create Firewall Rule**.
3. **Name**: `allow-pothole-backend`
4. **Targets**: `All instances in the network`
5. **Source IPv4 ranges**: `0.0.0.0/0`
6. **Protocols and ports**: checked `tcp` and enter `8000`.
7. Click **Create**.

## Step 3: Connect to your VM
1. In the VM Instances list, click **SSH** next to your new instance.
2. A terminal window will open in your browser.

## Step 4: Transfer Your Code
You can either clone from GitHub (easiest) or upload files.

### Option A: Using Git (Recommended)
If your code is on GitHub:
```bash
sudo apt update
sudo apt install git -y
git clone <YOUR_GITHUB_REPO_URL>
cd <YOUR_REPO_NAME>
```

### Option B: Uploading Zip
1. Zip your project folder locally.
2. In the SSH window, click the **Upload File** (gear icon) -> **Upload file**.
3. Upload `project.zip`.
4. Unzip it:
   ```bash
   sudo apt install unzip -y
   unzip project.zip
   cd project
   ```

## Step 5: Install Dependencies (Run on VM)
Run the following commands in the SSH terminal:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

## Step 6: Test the Server
Run the server manually to check for errors:
```bash
python3 backend/main.py
```
If it says `Uvicorn running on http://0.0.0.0:8000`, it's working!
- Press `Ctrl+C` to stop it.

## Step 7: Run in Background (Keep Alive)
To keep the server running even after you close the SSH window, we use `systemd`.

1. **Create a service file**:
   ```bash
   sudo nano /etc/systemd/system/pothole-backend.service
   ```

2. **Paste the configuration** (Modify paths if needed):
   ```ini
   [Unit]
   Description=Pothole Detection Backend
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/home/<YOUR_USERNAME>/<PROJECT_FOLDER>
   ExecStart=/home/<YOUR_USERNAME>/<PROJECT_FOLDER>/venv/bin/python3 backend/main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   *Replace `<YOUR_USERNAME>` with your username (run `whoami` to check) and `<PROJECT_FOLDER>` with your folder name.*
   *Press `Ctrl+O`, `Enter`, then `Ctrl+X` to save and exit.*

3. **Start the Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start pothole-backend
   sudo systemctl enable pothole-backend
   ```

4. **Check Status**:
   ```bash
   sudo systemctl status pothole-backend
   ```

## Step 8: Access the API
Your API is now live at:
`http://<YOUR_VM_EXTERNAL_IP>:8000/api/potholes`

You can now update your `add_potholes_remote.py` locally with this new IP!
