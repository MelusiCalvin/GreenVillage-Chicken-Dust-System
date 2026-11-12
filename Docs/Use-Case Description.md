# 3.2 Use-Case Description: Record Chicken Purchase
## 3.2.1 Use-case information
**Item	            Description**

Use-case ID	        UC-01
Use-case name	    Record Chicken Purchase
Primary actor	    Owner
Supporting actors	Manager, authorised Employee
Category	        Inventory and Purchasing
Priority	        High
Trigger	            A new chicken purchase is received by the business.

## 3.2.2 Preconditions
Before this use case can begin:

1. The user must be logged into ChickenHub.
2. The user must have permission to record purchases.
3. The chicken purchase details must be available.
4. The purchasing information must be ready for capturing.

## 3.2.3 Main success scenario
The following describes the normal process:

Step	        Actor / System	        Action
1	            User	                Opens the inventory or purchasing section.
2	            User	                Selects Record Chicken Purchase.
3	            System	                Displays the purchase registration form.
4	            User	                Enters the purchase date and supplier details.
5	            User	                Enters the quantity of chickens purchased.
6	            User	                Enters the total purchase price.
7	            User	                Enters any discount received.
8	            System	                Calculates the average cost per chicken and final purchase amount.
9	            User	                Reviews and submits the purchase information.
10	            System	                Validates the information and saves the purchase.
11	            System	                Updates the available chicken stock.
12	            System	                Displays a purchase confirmation.

## 3.2.4 Alternative and exception flows
**Scenario	                            System response**
Required information is missing	        Displays validation messages.
Quantity is zero or negative	        Rejects the purchase entry.
Purchase price is invalid	            Requests a valid amount.
Discount exceeds the purchase amount	Rejects the entry and requests correction.
User does not have permission	        Prevents access to the purchase function.
Database error occurs	                Does not confirm the purchase or update stock, informs the user that saving failed.

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
**Item	                Description**
Use-case ID	            UC-02
Use-case name	        Record Ingredient Purchase
Primary actor	        Owner
Supporting actors	    Manager, authorised Employee
Category	            Inventory and Purchasing
Priority	            High
Trigger	                The business purchases ingredients or supplies.

## 3.3.2 Preconditions
1. The user must be logged into ChickenHub.
2. The user must have permission to record purchases.
3. The ingredient or supply must be identified.
4. The purchase details must be available.

## 3.3.3 Main success scenario
**Step	Actor / System	        Action**
1	    User	                Opens the purchasing section.
2	    User	                Selects Record Ingredient Purchase.
3	    System	                Displays the ingredient purchase form.
4	    User	                Selects an existing ingredient or adds a new one.
5	    User	                Enters the purchase date and supplier.
6	    User	                Enters the quantity purchased and unit of measurement.
7	    User	                Enters the unit price and any discount.
8	    System	                Calculates the total purchase amount.
9	    User	                Reviews and submits the information.
10	    System	                Validates and saves the purchase.
11	    System	                Updates the ingredient's available stock.
12	    System	                Displays a purchase confirmation.

## 3.3.4 Alternative and exception flows
**Scenario	                            System response**
Ingredient is not registered	        Allows an authorised user to add it.
Required information is missing	        Displays validation messages.
Quantity is invalid	                    Rejects the purchase entry.
Unit price is invalid	                Requests a valid amount.
Discount exceeds the purchase amount	Rejects the entry.
User lacks permission	                Prevents the operation.
Saving fails	                        Does not update stock and displays an error.

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