#!/bin/bash
# Vercel build script for frontend

echo "Installing frontend dependencies..."
npm ci

echo "Building frontend..."
npm run build

echo "Frontend build completed successfully!"
