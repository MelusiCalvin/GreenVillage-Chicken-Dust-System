# 2.1 Stakeholder Identification
- ChickenHub: will serve four main stakeholder groups.
- **Stakeholder: Responsibilities**
- Business owner: Oversees business operations and accesses business information.
- Wife / Manager: Helps manage purchases, stock, sales, expenses and orders.
- Employees: Capture relevant transactions and assist with order processing.
- Customers: Browse meals, place orders and collect purchases.

# 2.2 Functional Requirements
Functional requirements describe the tasks that the system must perform

### FR01 – User Authentication and Access Control
- The system must allow authorised business users to log in securely.
- The system must support different user roles, including owner, manager and employee.
- The system must restrict access to features according to assigned permissions.
- The system must allow users to log out.

### FR02 – Chicken Purchasing Management
- The system must allow authorised users to record chicken purchases.
- The system must capture purchase dates, quantities, supplier details, purchase prices and discounts.
- The system must calculate the average purchase cost per chicken.
- The system must maintain a history of chicken purchases.
- The system must update inventory when purchases are recorded.

### FR03 – Ingredient and Supplies Management
- The system must allow users to record purchases of ingredients and other business supplies.
- The system must capture item names, quantities, unit prices and purchase dates.
- The system must maintain records of ingredient purchases.
- The system must support stock quantity updates.

### FR04 – Inventory Management
- The system must display available stock quantities.
- The system must record stock received, used, sold and adjusted.
- The system must maintain a history of inventory movements.
- The system must allow authorised users to correct stock records with an appropriate reason.
- The system should provide low-stock notifications.

### FR05 – Product and Meal Management
- The system must allow authorised users to manage products and meal options.
- The initial product catalogue must support full, half and quarter chicken options.
- The system must support meal accompaniments such as pap, gravy and salsa.
- The system must allow authorised users to maintain product prices.

### FR06 – Sales Management
- The system must allow employees to record walk-in sales.
- The system must record products sold, quantities, prices, dates and payment information.
- The system must maintain a searchable sales history.
- The system must calculate sales totals.

### FR07 – Expense Management
- The system must allow authorised users to record business expenses.
- The system must capture expense descriptions, categories, dates and amounts.
- The system must maintain an expense history.

### FR08 – Online Customer Ordering
- The system must allow customers to view available meals and prices.
- The system must allow customers to select products and quantities.
- The system must provide a shopping cart.
- The system must allow customers to submit orders for collection.
- The system must provide customers with an order reference.

### FR09 – Order Management
- The system must allow employees to view incoming customer orders.
- The system must support order statuses such as pending, accepted, preparing, ready and collected.
- The system must allow authorised employees to update order statuses.
- The system must maintain order history.

### FR10 – Reports and Historical Records
- The system must maintain digital records from its implementation date.
- The system must allow authorised users to search historical sales, purchases, expenses and inventory movements.
- The system must generate daily, weekly and monthly business reports.
- The system should provide revenue, expenses and estimated profit summaries.

# Non-functional Requirements
These describe the quality standards ChickenHub should meet

**ID    Requirement         Description**
NFR01	Usability	        The system should be simple to understand and operate.
NFR02	Security	        User accounts and business information must be protected.
NFR03	Performance	        Common operations should respond within a reasonable time.
NFR04	Reliability	        The system should process and store business records consistently.
NFR05	Data integrity	    Transactions and stock updates must not produce inconsistent records.
NFR06	Maintainability	    The application should be structured to support future improvements.
NFR07	Accessibility	    The interface should work on desktop computers, tablets and smartphones.
NFR08	Data backup	        Business records should be backed up regularly to reduce the risk of data loss.

# 2.4 Business rules
These are rules that the application must follow:

- Only authorised users may access business management features.
- Every purchase must have a recorded date and quantity.
- Every sale must have identifiable transaction details.
- Stock quantities must be updated when purchases and stock-consuming activities are recorded.
- A customer order must have an identifiable order reference.
- Historical records must remain available for authorised review.
- Changes to stock quantities must be recorded so that the business can trace adjustments.
- Financial reports must distinguish revenue, expenses and estimated profit.

# 2.5 Assumptions and outstanding decisions
The following details still need confirmation from the business:

- Whether customers can customise meal accompaniments.
- Preferred payment methods.
- Whether online orders require payment before collection.
- Whether employees can record expenses or only the owner and manager.