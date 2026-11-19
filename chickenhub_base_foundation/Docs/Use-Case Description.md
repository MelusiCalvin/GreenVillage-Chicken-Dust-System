# 3.2 Use-Case Description: Record Chicken Purchase
## 3.2.1 Use-case information
| **Item**	      |      **Description** |
| --- | --- |
| Use-case ID	    |    UC-01 |
| Use-case name	|    Record Chicken Purchase |
| Primary actor	|    Owner |
| Supporting actors |	Manager, authorised Employee |
| Category	  |      Inventory and Purchasing |
| Priority	  |      High |
| Trigger	      |      A new chicken purchase is received by the business. |

## 3.2.2 Preconditions
Before this use case can begin:

1. The user must be logged into ChickenHub.
2. The user must have permission to record purchases.
3. The chicken purchase details must be available.
4. The purchasing information must be ready for capturing.

## 3.2.3 Main success scenario
The following describes the normal process:

| Step	|        Actor / System	    |    Action |
| --- | --- | --- |
| 1	    |        User	       |         Opens the inventory or purchasing section. |
| 2	     |       User	      |          Selects Record Chicken Purchase. |
| 3	     |       System	      |          Displays the purchase registration form. |
| 4	     |       User	       |         Enters the purchase date and supplier details. |
| 5	     |       User	      |          Enters the quantity of chickens purchased. |
| 6	     |       User	       |         Enters the total purchase price. |
| 7	     |       User	       |         Enters any discount received. |
| 8	     |       System	       |         Calculates the average cost per chicken and final purchase amount. |
| 9	     |       User	        |        Reviews and submits the purchase information. |
| 10	  |          System	    |            Validates the information and saves the purchase. |
| 11	 |           System	    |            Updates the available chicken stock. |
| 12	 |           System	    |            Displays a purchase confirmation. |

## 3.2.4 Alternative and exception flows
| **Scenario**                  |      **System response**|
| --- | --- |
| Required information is missing	   |     Displays validation messages.|
| Quantity is zero or negative	   |     Rejects the purchase entry.|
| Purchase price is invalid	     |       Requests a valid amount.|
| Discount exceeds the purchase amount |	Rejects the entry and requests correction.|
| User does not have permission	  |      Prevents access to the purchase function.|
| Database error occurs	         |       Does not confirm the purchase or update stock, informs the user that saving failed.|

## 3.2.5 Business calculations
ChickenHub should calculate the following:

Average cost per chicken: 
    average cost = total purchase price/Quantity Purchased
Final purchase amount:
    final amount = total purchase price - discount

## 3.2.6 Postconditions

After successful completion:
1. The chicken purchase is stored in the database.
2. The available whole-chicken stock increases by the quantity purchased.
3. The purchase is included in the historical purchasing records.
4. The system stores the user who recorded the purchase.
5. The purchase information becomes available for reporting.

## 3.2.7 Expected outcome

The business can record chicken purchases digitally, maintain accurate stock quantities and retrieve previous purchasing information without searching through physical books.

# 3.3 Use-Case Description: Record Ingredient Purchase
## 3.3.1 Use-case information
| **Item**        |   **Description** |
| --- | --- |
| Use-case ID	        |    UC-02 |
| Use-case name	    |    Record Ingredient Purchase |
| Primary actor	    |    Owner |
| Supporting actors	|    Manager, authorised Employee |
| Category	        |    Inventory and Purchasing |
| Priority	        |    High |
| Trigger	             |   The business purchases ingredients or supplies. |

## 3.3.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have permission to record purchases.
3. The ingredient or supply must be identified.
4. The purchase details must be available.

## 3.3.3 Main success scenario
| **Step** | 	**Actor / System**	      | ** Action**  |
| --- | --- | --- |
| 1	   |  User	              |  Opens the purchasing section. |
| 2	   |  User	              |  Selects Record Ingredient Purchase. |
| 3	   |  System	              |  Displays the ingredient purchase form. |
| 4	  |   User	              |  Selects an existing ingredient or adds a new one. |
| 5	  |   User	              |  Enters the purchase date and supplier. |
| 6	  |   User	              |  Enters the quantity purchased and unit of measurement. |
| 7	  |   User	              |  Enters the unit price and any discount. |
| 8	  |   System	              |  Calculates the total purchase amount. |
| 9	  |   User	              |  Reviews and submits the information. |
| 10	  |   System	              |  Validates and saves the purchase. |
| 11	  |   System	              |  Updates the ingredient's available stock. |
| 12	  |   System	              |  Displays a purchase confirmation. |

## 3.3.4 Alternative and exception flows
| **Scenario**                 |    **System response** |
| --- | --- |
| Ingredient is not registered	    |    Allows an authorised user to add it. |
| Required information is missing	    |    Displays validation messages. |
| Quantity is invalid	                |    Rejects the purchase entry. |
| Unit price is invalid	            |    Requests a valid amount. |
| Discount exceeds the purchase amount |	Rejects the entry. |
| User lacks permission	         |       Prevents the operation. |
| Saving fails	                 |       Does not update stock and displays an error. |

## 3.3.5 Postconditions
1. The ingredient purchase is saved.
2. The ingredient's stock quantity is increased.
3. The purchase is included in historical purchasing records.
4. The system records who captured the purchase.
5. The information is available for reporting.

## 3.3.6 Expected outcome
The business can digitally record purchases of ingredients and supplies, monitor available quantities and retrieve historical purchasing information.

# 3.4 Use-Case Description: Manage Inventory
This use case covers what happens to stock after it has been purchased.

For ChickenHub, inventory management is particularly important because whole chickens are used to prepare full, half and quarter chicken meals. Ingredients are also consumed during meal preparation.

## 3.4.1 Use-case information
| **Item**	      |      **Description**|
| --- | --- |
| Use-case ID	    |    UC-03|
| Use-case name	|    Manage Inventory|
| Primary actor	|    Owner|
| Supporting actors	Manager, authorised Employee|
| Category	   |     Inventory Management|
| Priority	   |     High
| Trigger	       |     A user needs to view, update or adjust stock information.|

## 3.4.2 Preconditions
1. The user must be authenticated.
2. The user must have inventory permissions.
3. The relevant stock item must exist in the system.

## 3.4.3 Main success scenario
| **Step** | **Actor / System** | **Action** |
| --- | --- | --- |
| 1	| User |	Opens the inventory dashboard. |
| 2	| System |	Displays available stock items and quantities. |
| 3	| User |	Selects a stock item. |
| 4	| System |	Displays the item's stock information and movement history. |
| 5	| User |	Selects an inventory action. |
| 6	| User |	Records stock received, used, wasted or adjusted. |
| 7	| User |	Provides the quantity and reason where applicable. |
| 8	| System |	Validates the information. |
| 9	| System |	Updates the stock balance. |
| 10| System |	Records the stock movement in the history. |
| 11| System |	Displays confirmation. |

## 3.4.4 Inventory actions
| **Action** |	**Description** |
| --- | --- |
| Stock received |	Adds newly purchased items to inventory. |
| Stock used |	Records ingredients used during meal preparation. |
| Stock sold |	Records stock consumed through sales. |
| Stock wasted |	Records spoiled or unusable stock. |
| Stock adjustment |	Corrects stock quantities with a recorded reason. |

Important: ChickenHub must avoid counting the same chicken twice. For example, if a whole chicken is divided into portions, the system must transfer its quantity into the relevant portion stock rather than treating the portions as newly purchased chickens.

## 3.4.5 Postconditions

- Stock quantities are updated.
- Every stock movement is recorded.
- Historical inventory information is available.
- Users can review previous stock activities.

## 3.4.6 Expected outcome

The business can monitor its inventory digitally, understand how stock changes and identify discrepancies without relying entirely on physical stock books.

# 3.5 UC-04: Record Walk-in Sale
## 3.5.1 Use-case information
| **Item**	| **Description** |
| --- | --- |
| Use-case ID	| UC-04 |
| Use-case name	| Record Walk-in Sale |
| Primary actor	| Employee |
| Supporting actors	| Owner, Manager |
| Category	| Sales Management |
| Priority	| High |
| Trigger	| A customer purchases food directly from the business. |

## 3.5.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have permission to record sales.
3. Products and selling prices must be configured.
4. Relevant stock must be available.

## 3.5.3 Main success scenario

| **Step**	| **Actor / System**	| **Action** |
| --- | --- | --- |
| 1	| Employee	| Opens the sales section. |
| 2	| Employee	| Selects Record Walk-in Sale. |
| 3	| System	| Displays available products and meals. |
| 4	| Employee	| Selects the customer's requested meal. |
| 5	| Employee	| Enters the quantity purchased. |
| 6	| System	| Calculates the total selling amount. |
| 7	| Employee	| Selects the payment method. |
| 8	| Employee	| Confirms the transaction. |
| 9	| System	| Validates the sale information. |
| 10	| System	| Saves the transaction. |
| 11	| System	| Updates the relevant stock records. |
| 12	| System	| Displays a sales confirmation. |

## 3.5.4 Alternative and exception flows

| **Scenario**	| **System response** |
| --- | --- |
| Required information is missing	| Displays validation messages. |
| Product is unavailable	| Informs the employee that the product cannot be sold. |
| Insufficient stock	| Prevents the sale from being completed. |
| Invalid quantity	| Requests a valid quantity. |
| Payment information is missing	| Requests the missing information. |
| Database error occurs	| Does not confirm the transaction or update stock. |

## 3.5.5 Postconditions
1. The sale is saved in the database.
2. Relevant inventory quantities are updated.
3. The transaction is added to sales history.
4. The system records the user who processed the sale.
5. The transaction becomes available for reporting.

## 3.5.6 Expected outcome
The business can digitally record walk-in sales, maintain accurate sales history and monitor daily revenue.

# 3.6 Use-Case: Manage Expenses
## 3.6.1 Use-case information
| **Item**	| **Description** |
| --- | --- |
| Use-case ID	| UC-05 |
| Use-case name	| Manage Expenses |
| Primary actor	| Owner |
| Supporting actors	| Manager, authorised Employee |
| Category	| Financial Management |
| Priority	| High |
| Trigger	| The business incurs an operational expense. |

## 3.6.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have permission to record expenses.
3. The expense information must be available.

## 3.6.3 Main success scenario
| **Step**	| **Actor / System**	| **Action** |
| --- | --- | --- |     
| 1	| User	| Opens the expense management section. |
| 2	| User	| Selects Add Expense. |
| 3	| System	| Displays the expense registration form. |
| 4	| User	| Enters the expense description. |
| 5	| User	| Selects an expense category. |
| 6	| User	| Enters the expense date. |
| 7	| User	| Enters the amount paid. |
| 8	| User	| Provides payment information and additional notes where applicable. |
| 9	| User	| Reviews and submits the expense. |
| 10	| System	| Validates the expense information. |
| 11	| System	| Saves the expense record. |
| 12	| System	| Displays confirmation. |

## 3.6.4 Alternative and exception flows
| **Scenario**	| **System response** |
| --- | --- |
| Required information is missing	| Displays validation messages. |
| Invalid expense amount	| Requests a valid amount. |
| Expense category is missing	| Requests a category. |
| User lacks permission	| Prevents access to the expense function. |
| Database error occurs	| Does not confirm the expense. |

## 3.6.5 Postconditions
1. The expense is saved in the database.
2. The expense appears in historical records.
3. The system records who captured the expense.
4. The expense becomes available for financial reporting.

## 3.6.6 Expected outcome
The business can record and retrieve operational expenses digitally, making it easier to monitor expenditure and calculate estimated profit.

# 3.7 UC-06: Manage Products and Prices
## 3.7.1 Use-case information
| **Item**	| **Description** |
| --- | --- | 
| Use-case ID	| UC-06 |
| Use-case name	| Manage Products and Prices |
| Primary actor	| Owner |
| Supporting actors	| Manager |
| Category	| Product Management |
| Priority	| High || 
| Trigger	| A new product is introduced or an existing product's information or price changes. |

## 3.7.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have product management permissions.
3. The product information must be available.

## 3.7.3 Main success scenario
| **Step**	| **Actor / System**	| **Action** | 
| --- | --- | --- |
| 1	| User	| Opens the product management section. | 
| 2	| User	| Selects Add Product or Edit Product. | 
| 3	| System	| Displays the product registration form. | 
| 4	| User	| Enters the product name and description. | 
| 5	| User	| Selects the product category. | 
| 6	| User	| Enters the selling price. | 
| 7	| User	| Sets the product's availability. | 
| 8	| User	| Reviews and submits the information. | 
| 9	| System	| Validates the product details. | 
| 10	| System	| Saves the product information. | 
| 11	| System	| Updates the product catalogue. | 
| 12	| System	| Displays confirmation. |  

## 3.7.4 Alternative and exception flows
| **Scenario**	| **System response** |
| --- | --- |
| Product name is missing	| Requests the product name. |
| Selling price is invalid	| Requests a valid amount. |
| Product already exists	| Alerts the user. |
| Required information is missing	| Displays validation messages. |
| User lacks permission	| Prevents access. |
| Database error occurs	| Does not confirm the changes. |

## 3.7.5 Postconditions
1. Product information is saved.
2. Product prices are updated.
3. Product availability is reflected in the catalogue.
4. Customers can view available products through the ordering page.

## 3.7.6 Expected outcome
The business can maintain its product catalogue, update meal prices and control which products are available for purchase.

# 3.8 Use-Case: Browse Menu
## 3.8.1 Use-case information
| **Item**	| **Description** |
| --- | --- | 
| Use-case ID	| UC-07 |
| Use-case name	| Browse Menu |
| Primary actor	| Customer |
| Supporting actors	| None |
| Category	| Customer Ordering |
| Priority	| High |
| Trigger	| A customer opens the ChickenHub online ordering page. |

## 3.8.2 Preconditions
1. The customer ordering page must be accessible.
2. Products must be registered in the system.
3. Product information and prices must be configured.

## 3.8.3 Main success scenario
| **Step**	| **Actor / System**	| **Action** |
| --- | --- | --- |
| 1	| Customer	| Opens the ChickenHub ordering page. |
| 2	| System	| Retrieves available products. |
| 3	| System	| Displays the menu. |
| 4	| Customer	| Browses the available meals. |
| 5	| Customer	| Selects a product. |
| 6	| System	| Displays the product description, options and price. |
| 7	| Customer	| Decides whether to continue browsing or place an order. |

## 3.8.4 Alternative and exception flows
| **Scenario**	| **System response** |
| --- | --- |
| No products are available	| Displays a message indicating that no meals are currently available. |
| Product is unavailable	| Marks the product as unavailable. |
| Product information cannot load	| Displays an error message. |

## 3.8.5 Postconditions
1. The customer has viewed the available menu.
2. The customer can proceed to select meals for an order.

## 3.8.6 Expected outcome
Customers can conveniently browse available meals and view their prices before placing an order.

# 3.9 Use-Case: Place Online Order
## 3.9.1 Use-case information
| **Item**	| **Description** |
| --- | --- |
| Use-case ID	| UC-08 |
| Use-case name	| Place Online Order |
| Primary actor	| Customer |
| Supporting actors	| Employee, Manager |
| Category	| Customer Ordering |
| Priority	| High |
| Trigger	| A customer decides to place an order online. |

## 3.9.2 Preconditions
1. The customer ordering page must be accessible.
2. At least one product must be available.
3. Product prices must be configured.
4. The customer must have selected at least one product.

## 3.9.3 Main success scenario
| Step	| Actor / System	| Action |
| --- | --- | --- |
| 1	| Customer	| Opens the online ordering page. |
| 2	| Customer	| Browses the available meals. |
| 3	| Customer	| Selects the desired meals. |
| 4	| Customer	| Adds selected meals to the shopping cart. |
| 5	| System	| Displays the selected products and quantities. |
| 6	| System	| Calculates the order total. |
| 7	| Customer	| Proceeds to checkout. |
| 8	| Customer	| Enters contact information. |
| 9	| Customer	| Selects a collection time, if supported. |
| 10	| Customer	| Reviews the order details. |
| 11	| Customer	| Submits the order. |
| 12	| System	| Validates the order information. |
| 13	| System	| Creates and saves the order. |
| 14	| System	| Generates an order reference. |
| 15	| System	| Displays order confirmation. |

## 3.9.4 Alternative and exception flows
| Scenario	| System response| 
| --- | --- | 
| Shopping cart is empty	| Prevents checkout.| 
| Product becomes unavailable	| Informs the customer and requests an alternative.| 
| Invalid contact information	| Requests correction.| 
| Collection time is unavailable	| Requests another collection time.| 
| Required information is missing	| Displays validation messages.| 
| Order submission fails	| Displays an error and does not confirm the order.| 

## 3.9.5 Postconditions
1. The online order is saved.
2. A unique order reference is generated.
3. The order appears in the business order management section.
4. The customer receives confirmation.
5. The order is available for processing.

## 3.9.6 Expected outcome
Customers can place food orders online in advance and arrange collection without having to place their orders at the physical counter.

# 3.10 Use-Case: Manage Customer Orders
## 3.10.1 Use-case information
| Item	| Description |
| --- | --- |
| Use-case ID	| UC-09 |
| Use-case name	| Manage Customer Orders |
| Primary actor	| Employee |
| Supporting actors	| Owner, Manager |
| Category	| Order Management |
| Priority	| High |
| Trigger	| A new online customer order is received. |

## 3.10.2 Preconditions
1. The employee must be logged into ChickenHub.
2. The employee must have order management permissions.
3. Customer orders must exist in the system.

## 3.10.3 Main success scenario
| Step	| Actor / System	| Action |
| --- | --- | --- |
| 1	| Employee	| Opens the order management section. |
| 2	| System	| Displays incoming customer orders. |
| 3	| Employee	| Selects an order. |
| 4	| System	| Displays the order details. |
| 5	| Employee	| Reviews the order. |
| 6	| Employee	| Accepts the order. |
| 7	| System	| Updates the status to Accepted. |
| 8	| Employee	| Begins preparing the order. |
| 9	| Employee	| Updates the status to Preparing. |
| 10	| Employee	| Marks the order as Ready when preparation is complete. |
| 11	| Employee	| Confirms that the customer has collected the order. |
| 12	| System	| Updates the status to Collected. |
| 13	| System	| Saves the updated order history. |

## 3.10.4 Alternative and exception flows
Scenario	System response
Order cannot be fulfilled	Allows the employee to reject it with a reason.
Customer requests cancellation	Updates the order if cancellation is permitted.
Order does not exist	Displays an appropriate message.
Invalid status transition	Prevents the status update.
Database error occurs	Does not confirm the status change.

## 3.10.5 Postconditions
1. The order status is updated.
2. The order history is maintained.
3. The customer can view the latest order status.
4. The completed order remains available for historical reporting.

## 3.10.6 Expected outcome
The business can receive, process and monitor online orders from submission until collection.

# 3.11 Use-Case: Search Historical Records
## 3.11.1 Use-case information
| Item	| Description |
| --- | --- |
| Use-case ID	| UC-10 |
| Use-case name	| Search Historical Records |
| Primary actor	| Owner |
| Supporting actors	| Manager, authorised Employee |
| Category	| Record Management |
| Priority	| Very High |
| Trigger	| A user needs to retrieve previously recorded business information. |

## 3.11.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have permission to access the relevant records.
3. Relevant records must exist in the database.

## 3.11.3 Main success scenario
| Step	| Actor / System	| Action |
| --- | --- | --- |
| 1	| User	| Opens the historical records section. |
| 2	| System	| Displays available record categories. |
| 3	| User	| Selects a category. |
| 4	| System	| Displays available search filters. |
| 5	| User	| Enters a date range or search criteria. |
| 6	| User	| Submits the search request. |
| 7	| System	| Searches the database. |
| 8	| System	| Retrieves matching records. |
| 9	| System	| Displays the search results. |
| 10	| User	| Selects a record to view its details. |
| 11	| System	| Displays the selected record. |

## 3.11.4 Alternative and exception flows
| Scenario	| System response |
| --- | --- |
| No matching records exist	| Displays a no-results message. |
| Invalid date range	| Requests correction. |
| Search criteria are incomplete	| Requests the required information. |
| User lacks permission	| Prevents access to restricted records. |
| Database error occurs	| Displays an error message. |

## 3.11.5 Postconditions
1. Matching historical records are displayed.
2. The user can review the selected record.
3. No original business records are changed by the search.

## 3.11.6 Expected outcome
The owner and authorised employees can retrieve historical business information quickly without manually searching through physical record books.

# 3.12 Use-Case: Generate Business Reports
## 3.12.1 Use-case information
| Item	| Description |
| --- | --- |
| Use-case ID	| UC-11 |
| Use-case name	| Generate Business Reports |
| Primary actor	| Owner |
| Supporting actors	| Manager |
| Category	| Reporting and Analytics |
| Priority	| High |
| Trigger	| The owner or manager needs to review business performance. |

## 3.12.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have reporting permissions.
3. Relevant business records must exist.

## 3.12.3 Main success scenario
| Step	| Actor / System	| Action |
| --- | --- | --- |
| 1	| User	| Opens the reports section. |
| 2	| System	| Displays available report categories. |
| 3	| User	| Selects a report type. |
| 4	| System	| Displays reporting period options. |
| 5	| User	| Selects a reporting period. |
| 6	| User	| Requests the report. |
| 7	| System	| Retrieves relevant business records. |
| 8	| System	| Calculates the required totals. |
| 9	| System	| Generates the report. |
| 10	| System	| Displays the report. |
| 11	| User	| Reviews the report information. |

## 3.12.4 Alternative and exception flows
| Scenario	| System response |
| --- | --- | 
| No records exist for the selected period	| Displays a message indicating no available data. |
| Invalid date range	| Requests correction. |
| Calculation fails	| Displays an error message. |
| User lacks permission	| Prevents access to the report. |

## 3.12.5 Postconditions
1. The requested report is generated.
2. Relevant business information is summarised.
3. The report can be reviewed by authorised users.

## 3.12.6 Expected outcome
The business owner can monitor revenue, expenses, purchasing activities, inventory and estimated profit over different periods.

# 3.13 Use-Case: Manage User Accounts
## 3.13.1 Use-case information
| Item	| Description | 
| --- | --- |
| Use-case ID	| UC-12 | 
| Use-case name	| Manage User Accounts | 
| Primary actor	| Owner | 
| Supporting actors	| Manager, where authorised | 
| Category	| User Management | 
| Priority	| High | 
| Trigger	| A new employee needs access or an existing user's account requires modification. | 

## 3.13.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have account management permissions.
3. The required user information must be available.

## 3.13.3 Main success scenario
| Step	| Actor / System	|Action |
| --- | --- | --- |
| 1	| Owner	| Opens the user management section. |
| 2	| System	| Displays registered user accounts. |
| 3	| Owner	| Selects Add User. |
| 4	| System	| Displays the user registration form. |
| 5	| Owner	| Enters the user's details. |
| 6	| Owner	| Assigns a user role. |
| 7	| Owner	| Submits the information. |
| 8	| System	| Validates the information. |
| 9	| System	| Creates the user account. |
| 10	| System	| Assigns the selected permissions. |
| 11	| System	| Displays confirmation. |

## 3.13.4 Alternative and exception flows
| Scenario	| System response |
| --- | --- |
| Username already exists	| Requests a different username. |
| Required details are missing	| Displays validation messages. |
| Invalid role is selected	| Rejects the assignment. |
| User lacks permission	| Prevents access. |
| Database error occurs	| Does not confirm account creation. |

## 3.13.5 Postconditions
1. The user account is created or updated.
2. The assigned role is saved.
3. The user's permissions are applied.
4. The account becomes available for authentication.

## 3.13.6 Expected outcome
The owner can manage system users and control access to business information and functionality.

# 3.14 UC-13: View Order Status
## 3.14.1 Use-case information
| Item	| Description |
| --- | --- |
| Use-case ID	| UC-13 |
| Use-case name	| View Order Status |
| Primary actor	| Customer |
| Supporting actors	| None |
| Category	| Customer Ordering |
| Priority	| Medium |
| Trigger	| A customer wants to check the progress of a submitted order. |

## 3.14.2 Preconditions
1. The customer must have submitted an order.
2. A valid order reference must be available.
3. The order must exist in the system.

## 3.14.3 Main success scenario
| Step	| Actor / System	Action| 
| --- | --- |
| 1	| Customer	| Opens the order tracking page. | 
| 2	| System	| Displays the order tracking form. | 
| 3	| Customer	| Enters the order reference. | 
| 4	| Customer	| Submits the reference. | 
| 5	| System	| Validates the order reference. | 
| 6	| System	| Retrieves the corresponding order. | 
| 7	| System	| Displays the current order status. | 
| 8	| Customer	| Reviews the order progress. | 

## 3.14.4 Alternative and exception flows
| Scenario	| System response |
| --- | --- |
| Invalid order reference	| Displays an error message. |
| Order cannot be found	| Informs the customer. |
| Order has been collected	| Displays the completed status. |
| Order information cannot load	| Displays an error message. |

## 3.14.5 Postconditions
1. The customer can view the order's current status.
2. No order information is modified.
3. The order remains available for further processing where applicable.

## 3.14.6 Expected outcome
Customers can conveniently check whether their orders are pending, accepted, being prepared, ready for collection or already collected.

# 3.15 Consolidated Use-Case Register
| ID |	Use case |	Primary actor |
| --- | --- | --- |
| UC-01 |	Record Chicken Purchase |	Owner |
| UC-02 |	Record Ingredient | Purchase	Owner |
| UC-03 |	Manage Inventory |	Owner |
| UC-04 |	Record Walk-in Sale |	Employee |
| UC-05 |	Manage Expenses |	Owner |
| UC-06 |	Manage Products and Prices |	Owner |
| UC-07 |	Browse Menu |	Customer |
| UC-08 |	Place Online Order |	Customer |
| UC-09 |	Manage Customer Orders |	Employee |
| UC-10 |	Search Historical Records |	Owner |
| UC-11 |	Generate Business Reports |	Owner |
| UC-12 |	Manage User Accounts |	Owner |
| UC-13 |	View Order Status |	Customer |

Documentation note: These use cases represent the proposed initial requirements. Permissions, payment methods, collection scheduling and exact stock deductions still need confirmation from the business.