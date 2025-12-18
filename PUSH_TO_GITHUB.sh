#!/bin/bash
# Push Zav Cloud Deployment to GitHub
# ===================================

# BEFORE RUNNING THIS:
# 1. Create a repository on GitHub at https://github.com/new
#    Name it: zav-hospital
# 2. Copy your repository URL from GitHub

# Then update the URL below and run this script

# Configuration
REPO_URL="https://github.com/YOUR_USERNAME/zav-hospital.git"
BRANCH="main"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  ZAV CLOUD DEPLOYMENT - PUSH TO GITHUB${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if repository URL is updated
if [[ "$REPO_URL" == *"YOUR_USERNAME"* ]]; then
    echo -e "${YELLOW}⚠️  Please update REPO_URL in this script first!${NC}"
    echo -e "${YELLOW}Replace YOUR_USERNAME with your actual GitHub username${NC}"
    exit 1
fi

echo -e "${BLUE}Pushing to: ${YELLOW}$REPO_URL${NC}"
echo ""

# Step 1: Add remote
echo -e "${BLUE}Step 1: Adding GitHub remote...${NC}"
git remote add origin "$REPO_URL"
echo -e "${GREEN}✅ Remote added${NC}"
echo ""

# Step 2: Rename branch to main
echo -e "${BLUE}Step 2: Ensuring main branch...${NC}"
git branch -M main
echo -e "${GREEN}✅ Branch is main${NC}"
echo ""

# Step 3: Push to GitHub
echo -e "${BLUE}Step 3: Pushing to GitHub...${NC}"
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ SUCCESS - CODE PUSHED TO GITHUB!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Your repository is now at:${NC}"
    echo -e "${YELLOW}$REPO_URL${NC}"
    echo ""
    echo -e "${BLUE}Next step - Deploy to Railway:${NC}"
    echo -e "${YELLOW}Follow RAILWAY_DEPLOYMENT_GUIDE.md${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}❌ Push failed. Check error message above.${NC}"
    echo -e "${YELLOW}Common issues:${NC}"
    echo -e "${YELLOW}  - Repository URL is incorrect${NC}"
    echo -e "${YELLOW}  - GitHub credentials not set up${NC}"
    echo -e "${YELLOW}  - Try using SSH instead of HTTPS${NC}"
fi
