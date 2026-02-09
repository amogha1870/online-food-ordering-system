
# Online Food Ordering System

## Project Overview
The Online Food Ordering System is a web-based application that allows customers to browse restaurant menus, place food orders, and track order status online. The system helps restaurants manage orders digitally, reducing manual errors and improving service efficiency.

---
## Branching Strategy

This project follows GitHub Flow.

- main branch contains stable production code.
- Feature branches are created for development work.
- Each feature is developed separately and merged into main after testing.

Example:
feature-login
feature-docker-setup

---
## Quick Start – Local Development

### Prerequisites
- Install Docker Desktop
- Install Git
- Install VS Code

### Steps to Run Project

1. Clone Repository
git clone <your-repo-link>

2. Navigate to project folder
cd online-food-ordering

3. Build Docker Image
docker build -t food-app .

4. Run Container
docker run -p 3000:3000 food-app
---
## Local Development Tools

- Visual Studio Code
- Git & GitHub
- Docker Desktop
- Command Prompt / Terminal
---

## Problem It Solves
Traditional food ordering methods such as phone calls or physical visits are time-consuming and prone to errors. Customers face long waiting times and lack order tracking. Restaurants struggle with manual order management. This system provides a centralized platform connecting customers, restaurants, and delivery personnel.

---

## Target Users (Personas)

### Customer
- Orders food online
- Browses menus
- Tracks order status

### Restaurant Staff
- Manages menu items
- Processes customer orders
- Updates order status

### Delivery Personnel
- Receives delivery assignments
- Updates delivery progress

### System Administrator
- Manages users and system operations
- Monitors system performance

---

## Vision Statement
To develop a simple, reliable, and user-friendly online food ordering platform that improves customer convenience and enhances restaurant order management efficiency.

---

## Key Features / Goals
- User registration and login
- Browse restaurant menus
- Add food items to cart
- Place food orders
- Track order status
- Restaurant admin dashboard for menu and order management

---

## Success Metrics
- Users can register and log in successfully
- Customers can place orders without errors
- Restaurants can manage orders efficiently
- At least 80% of users can operate the system without external help
- System runs without major bugs

---

## Assumptions & Constraints

### Assumptions
- Users have internet access
- Restaurants regularly update menus
- Orders are processed during working hours
- Users are familiar with basic web applications

### Constraints
- Limited academic development timeline
- Use of open-source technologies only
- Online payment integration is optional
- System should remain simple and easy to understand

## MoSCoW Prioritization

<img width="629" height="593" alt="image" src="https://github.com/user-attachments/assets/907a293c-80d0-4f7e-839c-373f4b956200" />

Must Have features are essential for core food ordering functionality.
Should Have features enhance usability and management.
Could Have features improve user experience but are not critical.
Won’t Have features are planned for future development phases.

