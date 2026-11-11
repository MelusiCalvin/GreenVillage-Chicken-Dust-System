```mermaid

flowchart LR
    %% Actors
    Owner([Owner])
    Manager([Manager])
    Employee([Employee])
    Customer([Customer])

    %% System boundary
    subgraph ChickenHub["ChickenHub Business Management System"]

        %% User management
        UC1([Manage User Accounts])

        %% Purchasing
        UC2([Record Chicken Purchases])
        UC3([Record Ingredient Purchases])

        %% Business management
        UC4([Manage Inventory])
        UC5([Manage Products and Prices])
        UC6([Record Walk-in Sales])
        UC7([Manage Expenses])
        UC8([View Business Reports])
        UC9([Search Historical Records])

        %% Order management
        UC10([Manage Customer Orders])
        UC11([Process Orders])
        UC12([Update Order Status])

        %% Customer functionality
        UC13([Browse Menu])
        UC14([Select Meals])
        UC15([Place Online Order])
        UC16([View Order Status])
    end

    %% Owner interactions
    Owner --> UC1
    Owner --> UC2
    Owner --> UC3
    Owner --> UC4
    Owner --> UC5
    Owner --> UC6
    Owner --> UC7
    Owner --> UC8
    Owner --> UC9
    Owner --> UC10

    %% Manager interactions
    Manager --> UC2
    Manager --> UC3
    Manager --> UC4
    Manager --> UC5
    Manager --> UC6
    Manager --> UC7
    Manager --> UC8
    Manager --> UC9
    Manager --> UC10

    %% Employee interactions
    Employee --> UC4
    Employee --> UC6
    Employee --> UC11
    Employee --> UC12

    %% Customer interactions
    Customer --> UC13
    Customer --> UC14
    Customer --> UC15
    Customer --> UC16

    %% Include relationships
    UC15 -.->|include| UC13
    UC15 -.->|include| UC14
    UC11 -.->|include| UC12

```