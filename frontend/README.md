# Cumpair Frontend - React/TypeScript Application

🔍 **Cumpair Frontend** is a modern React/TypeScript web application for AI-powered product analysis and price comparison.

## 🚀 Features

### 🖼️ Product Image Upload & Analysis

- Drag-and-drop image upload interface

- Real-time progress indicators

- Support for JPEG, PNG, WebP formats

- Image preview and cropping

### 📊 Price Comparison Matrix

- Interactive comparison table

- Real-time price updates

- Retailer logos and ratings

- Sorting and filtering options

### 📈 Trend Visualization

- Price history charts

- Interactive trend analysis

- Statistical insights

- Export capabilities

### 🎨 Modern UI/UX

- Tailwind CSS styling

- Responsive design

- Dark/light theme support

- Accessible components

## 🏗️ Tech Stack

- **React 18** with TypeScript

- **Vite** for fast development and building

- **Tailwind CSS** for styling

- **Shadcn/ui** component library

- **Recharts** for data visualization

- **React Query** for state management

- **React Router** for navigation

## 🚀 Development Setup

### Prerequisites

- Node.js 18+

- npm or yarn

### Installation

```text
bash
# Install dependencies

npm install

# Start development server

npm run dev

# Build for production

npm run build

# Preview production build

npm run preview

```text

### Environment Variables

Create a `.env.development` file:

```text
env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_MOCK_DATA=false

```text

## 🔧 API Integration

The frontend connects to the Cumpair backend API on port 8000:

### Development Proxy

- Vite dev server proxies `/api/` requests to `http://localhost:8000`

- Configured in `vite.config.ts`

### Production

- Nginx serves static files and proxies API requests

- Configured in `nginx.conf`

### API Endpoints Used

- `POST /api/v1/analyze` - Upload and analyze product images

- `GET /api/v1/analyze/{id}` - Get analysis results

- `GET /api/v1/compare/{id}` - Get price comparison data

- `POST /api/v1/compare/{id}/refresh` - Refresh price data

## 📁 Project Structure

```text

src/
├── components/          # Reusable UI components
│   ├── ui/             # Shadcn/ui components
│   └── custom/         # Custom components
├── pages/              # Page components
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── hooks/              # Custom React hooks
└── styles/             # Global styles

```text

### Edit a file directly in GitHub

- Navigate to the desired file(s).

- Click the "Edit" button (pencil icon) at the top right of the file view.

- Make your changes and commit the changes.

### Use GitHub Codespaces

- Navigate to the main page of your repository.

- Click on the "Code" button (green button) near the top right.

- Select the "Codespaces" tab.

- Click on "New codespace" to launch a new Codespace environment.

- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite

- TypeScript

- React

- shadcn-ui

- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/c045a815-50ed-4339-b4db-78c47640603a) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
