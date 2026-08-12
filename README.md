# trekking_management_application
# NomadTrails
*A Comprehensive Role-Based Trekking Management System*

## Project Overview
NomadTrails is a robust, full-stack web application designed to digitalize and streamline the management of outdoor adventure companies. Built primarily with Python and Flask, the platform solves the complex logistical challenge of coordinating between administrators, ground staff (guides), and trekkers. 

The application ensures that users can easily browse and book adventures, staff members can manage their assigned groups, and administrators have complete oversight of the entire business operation through a secure, data-driven dashboard.

---

## Core Features & Architecture

### 1. Advanced Role-Based Access Control (RBAC)
The core of NomadTrails is its strict security and routing architecture. The application is divided into three completely isolated portals using Flask Blueprints. Unauthorized users attempting to access protected routes are immediately intercepted and redirected.
*   **System Administrators:** Have absolute control. They can create new trekking packages, edit total slot capacities, blacklist malicious users, and approve pending staff registrations.
*   **Trek Staff / Guides:** Have restricted access. They can only view the specific treks assigned to them by an admin. They have the authority to view participant rosters and update the status of a trek (e.g., changing a trek to "Completed" once the trip finishes).
*   **Trekkers (Users):** The consumer-facing side. Users can browse a catalogue of adventures, filter by location or difficulty, book slots, and manage their own profile and history.

### 2. Dynamic Capacity Management
To prevent overbooking, NomadTrails features a real-time capacity engine. When a user clicks "Book", the system queries the database to ensure `available_slots > 0`. If successful, it automatically decrements the available slots. If a user cancels their booking, the system immediately refunds that slot back to the public pool.

### 3. Staff Approval Pipeline
Security is paramount. When someone registers for a "Staff" account, they are not immediately granted access to the system. Their account defaults to a `"pending"` state. An Administrator must log into the Admin Dashboard, review the staff member, and manually toggle their account to `"active"` before they can log in.

### 4. RESTful JSON API
To future-proof the application for potential mobile app integration, NomadTrails includes a dedicated API Blueprint (`/api/`). This endpoint bypasses the HTML frontend entirely, returning raw JSON data regarding open treks, user profiles, and booking statuses.

---

## Technical Stack
*   **Backend Framework:** Flask (Python 3)
*   **Database Management:** SQLite3 paired with Flask-SQLAlchemy (ORM) for secure, Pythonic database queries.
*   **Authentication & Security:** Werkzeug (`generate_password_hash` & `check_password_hash`) to ensure user passwords are cryptographically secured before database insertion. Flask Sessions are utilized for maintaining state.
*   **Frontend Design:** HTML5, CSS3, and Bootstrap 5 for a responsive, mobile-first grid layout.
*   **Templating Engine:** Jinja2 for dynamic HTML generation and template inheritance (`base.html`).

---

## Database Schema Design
The backend relies on a strictly normalized relational database consisting of three primary models:
1.  **Users Table:** Stores credentials, roles (`admin`, `staff`, `user`), and account statuses (`active`, `pending`, `blacklisted`).
2.  **Treks Table:** Stores adventure details including location, difficulty, duration, pricing, and dynamic slot counts. Contains a Foreign Key linking to the `Users` table to assign a specific staff member.
3.  **Bookings Table:** Acts as a junction table resolving the many-to-many relationship between Users and Treks. Tracks individual reservation timestamps and current booking statuses (Booked, Cancelled, Completed).

---

## Local Setup & Installation

To run NomadTrails on your local machine, ensure you have Python 3 installed, then follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/NomadTrails-App.git
   cd NomadTrails-App
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows Activation:
   venv\Scripts\activate
   # Mac/Linux Activation:
   source venv/bin/activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database:**
   *(Run the provided seed script to automatically generate the database file and populate it with test data, treks, and 50 random users).*
   ```bash
   python seed.py
   ```

5. **Boot the Flask Server:**
   ```bash
   flask run
   ```
6. **Access the Web App:** Open your web browser and navigate to `http://127.0.0.1:5000`

---

## Demo Testing Credentials
If you initialized the database using the `seed.py` script, you can immediately test the RBAC features using the following pre-generated accounts:

*   **Administrator Access:** 
    *   Username: `admin` 
    *   Password: `admin123`
*   **Staff / Guide Access:** 
    *   Username: `staff_jamie_1` 
    *   Password: `password123`
*   **Trekker / User Access:** 
    *   Username: `trekker_casey_1` 
    *   Password: `password123`

