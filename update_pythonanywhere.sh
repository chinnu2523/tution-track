#!/bin/bash

echo "🚀 Starting TuitionTrack + VMS Updates..."

# 1. Update Code
echo "📥 pulling latest code from GitHub..."
git stash
git fetch origin main
git reset --hard origin/main

# 2. Update Database & Admin
echo "⚙️  Syncing database schema and resetting admin password..."
python3 -c 'import hashlib, secrets, sqlite3, os; p="magi@1982"; s=secrets.token_hex(16); dk=hashlib.pbkdf2_hmac("sha256", p.encode("utf-8"), s.encode("utf-8"), 260000); h=f"{s}${dk.hex()}"; conn=sqlite3.connect("tuition.db"); cur=conn.cursor(); cur.execute("UPDATE admins SET password_hash=? WHERE username=?", (h, "magi")); conn.commit(); print("✅ Database & Admin Sync Complete!")'

echo ""
echo "✨ Update Successful!"
echo "👉 FINAL STEP: Go to the 'Web' tab in PythonAnywhere and click the 'Reload' button."
echo "🔗 Then log in at: https://tutiontrack.pythonanywhere.com"
