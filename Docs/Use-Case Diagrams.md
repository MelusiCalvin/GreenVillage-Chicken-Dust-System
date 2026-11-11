
usecaseDiagram
    actor Owner
    actor Manager
    actor Employee
    actor Customer

    rectangle "ChickenHub System" {
        (Log in) as UC1
        (Manage user accounts) as UC2
        (Record chicken purchases) as UC3
        (Record ingredient purchases) as UC4
        (Manage inventory) as UC5
        (Manage products and prices) as UC6
        (Record walk-in sales) as UC7
        (Manage expenses) as UC8
        (View business reports) as UC9
        (Search historical records) as UC10
        (Manage customer orders) as UC11

        (Browse menu) as UC12
        (Select meals) as UC13
        (Place online order) as UC14
        (View order status) as UC15
    }

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
    Owner --> UC11

    Manager --> UC1
    Manager --> UC3
    Manager --> UC4
    Manager --> UC5
    Manager --> UC6
    Manager --> UC7
    Manager --> UC8
    Manager --> UC9
    Manager --> UC10
    Manager --> UC11

    Employee --> UC1
    Employee --> UC5
    Employee --> UC7
    Employee --> UC11

    Customer --> UC12
    Customer --> UC13
    Customer --> UC14
    Customer --> UC15

    UC14 ..> UC12 : <<include>>
    UC14 ..> UC13 : <<include>>
