# 🚀 Portfolio Publisher

> A web application that allows users to create, customize, manage, publish, and share their professional portfolio with AI-powered assistance.

## 🌐 Live Demo

🔗 https://portfolio-publisher.onrender.com

## 📂 GitHub Repository

🔗 https://github.com/arahulroshan/Portfolio-Publisher

---

## 📌 Project Overview

Portfolio Publisher is a Flask-based web application designed to help students and professionals create their own personalized online portfolios without requiring advanced web development knowledge.

Users can manage their personal information, education, skills, projects, certificates, experience, resume, and social links. They can customize the appearance of their portfolio and publish it through a unique public URL.

The application also includes an AI-powered chatbot that helps users with portfolio-related guidance.

---

## 🎯 Objectives

- Create professional portfolios easily.
- Allow users to manage portfolio information from one dashboard.
- Provide customizable portfolio themes.
- Allow users to upload project images, certificates, profile photos, and resumes.
- Generate a public portfolio URL.
- Generate a QR code for sharing the portfolio.
- Provide AI-powered portfolio assistance.
- Store user data securely using PostgreSQL.
- Deploy the application online.

---

## ✨ Features

### 👤 User Management
- User registration
- User login and logout
- Secure password hashing
- Session-based authentication

### 📝 Profile Management
- Full name
- Phone number
- Location
- About section
- Profile photo

### 🎓 Education
- Add education details
- Update education information
- Display education on public portfolio

### 💡 Skills
- Add skills
- Edit skills
- Delete skills
- Display skills on portfolio

### 💻 Projects
- Add projects
- Project description
- Technologies used
- GitHub link
- Live demo link
- Main project image
- Multiple project screenshots
- Edit and delete projects
- Project details page

### 🏆 Certificates
- Add certificates
- Issuing organization
- Issue date
- Certificate link
- Certificate image
- Edit and delete certificates

### 💼 Experience
- Company name
- Job role
- Start date
- End date
- Experience description
- Edit and delete experience

### 📄 Resume
- Upload resume
- View resume
- Replace resume
- Delete resume

### 🔗 Social Links
- LinkedIn
- GitHub
- Email
- Portfolio link

### 🎨 Portfolio Customization
- Theme color
- Background color
- Font style
- Background style

### 🌐 Portfolio Publishing
- Publish portfolio
- Unpublish portfolio
- Generate public portfolio URL
- Share portfolio with others

### 📱 QR Code
- Automatically generate a QR code for the published portfolio.
- Useful for resumes, posters, presentations, and events.

### 🤖 AI Portfolio Assistant
- AI-powered chatbot
- Portfolio-related guidance
- Multiple chat sessions
- Chat history
- Context-aware responses using portfolio information

---

## 🏗️ System Architecture

```text
                ┌──────────────────┐
                │      User        │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  HTML / CSS / JS │
                │    Frontend      │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │   Flask Web App  │
                │     Backend      │
                └───────┬───┬──────┘
                        │   │
              ┌─────────┘   └──────────┐
              ▼                        ▼
      ┌────────────────┐       ┌────────────────┐
      │   PostgreSQL   │       │    Gemini AI   │
      │    Database    │       │    Chatbot     │
      └────────────────┘       └────────────────┘
                        │
                        ▼
                ┌──────────────────┐
                │ Public Portfolio │
                │   + QR Code      │
                └──────────────────┘
