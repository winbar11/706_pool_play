#!/bin/bash
npm install --legacy-peer-deps
npm run build
npx serve -s build -l $PORT