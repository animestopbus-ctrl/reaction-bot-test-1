#!/bin/bash

echo "🚀 Telegram Auto Reaction SaaS - Quick Start Script"
echo "===================================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - MONGODB_URL (from MongoDB Atlas)"
    echo "   - JWT_SECRET (generate with: openssl rand -base64 32)"
    echo "   - TELEGRAM_API_ID (from https://my.telegram.org)"
    echo "   - TELEGRAM_API_HASH (from https://my.telegram.org)"
    echo "   - TELEGRAM_BOT_TOKEN (from @BotFather)"
    echo "   - OWNER_TELEGRAM_ID (from @userinfobot)"
    echo "   - OWNER_PASSWORD (your secure password)"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python $python_version found"
echo ""

echo "📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create necessary directories
mkdir -p logs sessions
echo "✅ Created logs and sessions directories"
echo ""

echo "✨ Setup complete!"
echo ""
echo "To start the backend:"
echo "  1. cd backend"
echo "  2. source venv/bin/activate"
echo "  3. python main.py"
echo ""
echo "Or simply run:"
echo "  cd backend && source venv/bin/activate && python main.py"
echo ""
echo "📱 Bot will be available at your bot username"
echo "🌐 API will be available at http://localhost:8000"
echo "📊 API docs at http://localhost:8000/docs"
echo ""
echo "📖 Read DEPLOYMENT_GUIDE.md for Render.com deployment"
echo ""
echo "Made with ❤️  by The Updated Guys"
