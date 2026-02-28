
Online Food Ordering System (FoodieExpress)
Project Overview

FoodieExpress is a web-based Online Food Ordering System that allows customers to browse restaurant menus, place food orders, and track order status online. The system enables restaurants to manage orders digitally, reducing manual errors and improving operational efficiency.

Branching Strategy

This project follows GitHub Flow:

• The main branch contains stable production-ready code.
• Feature branches are created for new development tasks.
• Each feature is independently developed, tested, and then merged into main.

Example feature branches:

• feature-login
• feature-docker-setup
• feature-order-module

This workflow ensures controlled development and stable releases.

Quick Start – Local Development
Prerequisites

• Docker Desktop
• Git
• Visual Studio Code

Steps to Run the Project
git clone <repository-url>
cd online-food-ordering
docker build -t food-app .
docker run -p 3000:3000 food-app

Then open:

http://localhost:3000

Development Tools

• Visual Studio Code
• Git & GitHub
• Docker Desktop
• Command Prompt / Terminal

Problem It Solves

Traditional food ordering methods such as phone calls or in-person visits are time-consuming and prone to errors.

• Customers experience long wait times and lack real-time tracking.
• Restaurants struggle with manual order processing.

FoodieExpress provides a centralized digital platform connecting customers, restaurants, and delivery personnel, improving accuracy, speed, and convenience.

Target Users (Personas)
Customer

• Browse restaurants and menus
• Add items to cart
• Place and track orders

Restaurant Staff

• Manage menu items
• Process and update orders
• Track incoming requests

Delivery Personnel

• Receive delivery assignments
• Update delivery status

System Administrator

• Manage users
• Monitor system operations
• Ensure system stability

Vision Statement

To develop a simple, reliable, and user-friendly online food ordering platform that enhances customer convenience and improves restaurant order management efficiency.

Key Features

• User registration and authentication
• Browse restaurant menus
• Add food items to cart
• Place food orders
• Track order status
• Restaurant dashboard for managing menu and orders

Success Metrics

• Users can successfully register and log in
• Customers can place orders without errors
• Restaurants can manage orders efficiently
• At least 80% of users can use the system without external help
• System runs without critical bugs

Assumptions & Constraints
Assumptions

• Users have internet access
• Restaurants regularly update menus
• Orders are processed during working hours
• Users understand basic web navigation

Constraints

• Limited academic development timeline
• Use of open-source technologies only
• Online payment integration optional
• System kept simple for academic clarity

## MoSCoW Prioritization

<img width="629" height="593" alt="image" src="https://github.com/user-attachments/assets/907a293c-80d0-4f7e-839c-373f4b956200" />

-Must Have features are essential for core food ordering functionality.
-Should Have features enhance usability and management.
-Could Have features improve user experience but are not critical.
-Won’t Have features are planned for future development phases.

## Software Design

The FoodieExpress system uses a Layered Client–Server architecture combined with the MVC design pattern.  
This design separates the user interface, business logic, and data access layers, improving scalability, maintainability, and modular development.

### Architecture Diagram

![Architecture](docs/design/architecture.png)

### UI Design
User Interface Design

The user interface was designed using Figma with a focus on clarity, consistency, and ease of navigation.

Key Screens

• Login & Registration
• Restaurant Browsing
• Menu & Item Selection
• Cart Management
• Checkout
• Order Confirmation

UI Design Principles Applied

• Consistent button styling
• Clear feedback messages
• ₹ currency format for Indian users
• Structured layout with clean spacing
• Simple and intuitive navigation flow

Main Design Decisions

• Separated authentication module to maintain low coupling.
• Used layered architecture for scalability and maintainability.
• Modularized features (Cart, Orders, Menu) for high cohesion.
• Abstracted database access through the Model layer.
• Designed a consistent UI to improve usability and user confidence.
