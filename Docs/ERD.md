# 3.3 Entity Relationship Diagram (ERD)
## 3.3.1 Identification of Database Entities
The following entities are proposed for the first version of ChickenHub.

The database entities represent the main objects and activities that ChickenHub needs to manage. Each entity will store specific information and will be connected to other entities through relationships.

## A. User and Customer Management

### 1. UserAccount
Stores the accounts of people who are authorised to access the business management system.  

Proposed attributes:
- user_id (PK)
- first_name
- last_name
- username
- email
- password
- role
- is_active
- date_created

The role will identify whether the account belongs to the Owner, Manager or Employee. Django's authentication and permissions system can be used to manage these accounts.

### 2. Customer
Stores customer information for online orders.  

Proposed attributes:
- customer_id (PK)
- first_name
- last_name
- phone_number
- email
- date_registered

A customer may place multiple online orders.

## B. Supplier and Purchasing Management

### 3. Supplier

Stores information about suppliers from whom the business purchases chickens, ingredients and other supplies.
Proposed attributes:
- supplier_id (PK)
- supplier_name
- contact_person
- phone_number
- email
- address

### 4. Purchase

Stores the general details of each purchase made by the business.
Proposed attributes:
- purchase_id (PK)
- supplier_id (FK)
- purchase_date
- total_amount
- discount
- final_amount
- payment_method
- recorded_by (FK)

The purchase record will capture the overall transaction, while the individual items purchased will be stored separately.

### 5. PurchaseItem

Stores the individual items included in a purchase.
Proposed attributes:
- purchase_item_id (PK)
- purchase_id (FK)
- inventory_item_id (FK)
- quantity
- unit_price
- subtotal

This allows one purchase to contain multiple items, such as chickens, tomatoes, onions and maize meal.

## C. Inventory Management

### 6. InventoryItem

Stores the different items that the business tracks in its inventory.
Proposed attributes:
- inventory_item_id (PK)
- item_name
- item_type
- unit_of_measure
- quantity_on_hand
- reorder_level
- is_active

Examples include:
- Whole chickens
- Chicken portions
- Tomatoes
- Onions
- Maize meal
- Soup sachets

Other ingredients and supplies:
The item type will distinguish between raw ingredients, whole chickens, prepared portions and other supplies.

### 7. StockMovement

Records every movement or adjustment made to inventory.
Proposed attributes:
- movement_id (PK)
- inventory_item_id (FK)
- movement_type
- quantity
- movement_date
- reason
- recorded_by (FK)
- Movement types may include:
- Stock received
- Stock used
- Stock sold
- Stock wasted
- Stock adjusted

This entity will provide a history of stock changes.

### 8. ChickenProcessing

Records the processing of whole chickens into smaller portions.  

Proposed attributes:
processing_id (PK)
processing_date
whole_chicken_quantity
recorded_by (FK)
notes

### 9. ProcessingOutput

Records the portions produced from a chicken-processing activity.  

Proposed attributes:
processing_output_id (PK)
processing_id (FK)
inventory_item_id (FK)
quantity_produced

This allows ChickenHub to record how many portions were produced during processing. The actual portion quantities and yields will be confirmed with the business.

## D. Product and Meal Management

### 10. Product

Stores the meals and products offered for sale.  

Proposed attributes:
- product_id (PK)
- product_name
- description
- selling_price
- availability_status
- date_created

Examples include:
- Full chicken platter
- Half chicken platter
- Quarter chicken platter

### 11. Recipe

Stores the ingredient and stock requirements associated with preparing a particular product.  

Proposed attributes:
- recipe_id (PK)
- product_id (FK)
- instructions
- date_created

### 12. RecipeItem

Connects recipes to the inventory items required to prepare a meal.

Proposed attributes:
- recipe_item_id (PK)
- recipe_id (FK)
- inventory_item_id (FK)
- quantity_required

For example, a meal may require a particular chicken portion, pap, gravy and salsa. The actual quantities will be confirmed with the business.

## E. Sales and Order Management

### 13. Sale

Stores completed sales transactions, including walk-in sales and completed online orders.  

Proposed attributes:
- sale_id (PK)
- order_id (FK, optional)
- sale_date
- total_amount
- payment_method
- recorded_by (FK)

The optional order reference will connect a completed online order to its sale, preventing the same transaction from being counted twice.

### 14. SaleItem

Stores the individual products included in a sale.  

Proposed attributes:
- sale_item_id (PK)
- sale_id (FK)
- product_id (FK)
- quantity
- unit_price
- subtotal

The unit price will be saved at the time of the transaction so that later product price changes do not alter historical sales.

### 15. CustomerOrder

Stores online orders submitted by customers.  

Proposed attributes:
- order_id (PK)
- customer_id (FK)
- order_date
- collection_time
- order_status
- total_amount
- order_reference

Possible order statuses include Pending, Accepted, Preparing, Ready, Collected and Cancelled.

### 16. OrderItem

Stores the individual products included in a customer's online order.  

Proposed attributes:
- order_item_id (PK)
- order_id (FK)
- product_id (FK)
- quantity
- unit_price
- subtotal

## F. Financial Management

### 17. Expense

Stores business expenses that are recorded separately from stock purchases.  

Proposed attributes:
- expense_id (PK)
- expense_description
- expense_category
- expense_date
- amount
- payment_method
- recorded_by (FK)

Examples may include transport, electricity, maintenance and other operating expenses.

## 3.3.2 Summary of Proposed Entities

The initial database design contains 17 entities:
- UserAccount
- Customer
- Supplier
- Purchase
- PurchaseItem
- InventoryItem
- StockMovement
- ChickenProcessing
- ProcessingOutput
- Product
- Recipe
- RecipeItem
- Sale
- SaleItem
- CustomerOrder
- OrderItem
- Expense

These entities will form the foundation of the ChickenHub database design. Their relationships will be represented in the Entity Relationship Diagram in the next section.