# PantryTrack: architecture sketch

**Group 2 (Monday) · ECE 461L Phase 1, R1-3**

PantryTrack is a web app for tracking shared food inventory in a household. The assignment's HaaS model maps onto the domain directly: a **household** plays the role of a project, and a **food item** plays the role of a hardware set, with `capacity` (total units stocked) and `availability` (units not yet claimed).

## Architecture

```mermaid
flowchart TD
    subgraph browser["Browser"]
        UI["React client"]
        APICLIENT["api/inventory.js"]
    end

    subgraph server["Flask server"]
        ROUTES["app.py<br/>REST routes"]
        ENC["Encryption<br/>password hashing"]
        USERS["usersDatabase.py<br/>accounts, login"]
        HOUSE["projectsDatabase.py<br/>households, access guard"]
        ITEMS["hardwareDatabase.py<br/>stock, batches, claims"]
        HELP["freshness.py, itemIdentity.py<br/>pure helpers"]
    end

    subgraph db["MongoDB Atlas"]
        UC[("Users")]
        HC[("Households")]
        IC[("Items")]
    end

    UI --> APICLIENT
    APICLIENT -->|JSON over HTTP| ROUTES
    ROUTES --> ENC
    ENC --> USERS
    ROUTES --> HOUSE
    HOUSE --> ITEMS
    ITEMS --> HELP
    USERS --> UC
    HOUSE --> HC
    ITEMS --> IC

    classDef plain fill:#ffffff,stroke:#8a8a8a,stroke-width:1px,color:#1a1a1a
    class UI,APICLIENT,ROUTES,ENC,USERS,HOUSE,ITEMS,HELP,UC,HC,IC plain
    style browser fill:#f2f2f2,stroke:#c0c0c0,color:#1a1a1a
    style server fill:#f2f2f2,stroke:#c0c0c0,color:#1a1a1a
    style db fill:#f2f2f2,stroke:#c0c0c0,color:#1a1a1a
```

Three tiers. The React client never touches the database directly. Every value on screen comes back from a REST call. Credentials are encrypted on the way into the `Users` collection, and every inventory call passes through a household membership check before it can read or write stock.

The Flask server and the Atlas database are cloud-hosted, so the app is reachable by URL rather than run locally.

## User flow

```mermaid
flowchart TD
    START([Open app]) --> AUTH{Have an account?}
    AUTH -->|No| REG["Register<br/>userid + password"]
    AUTH -->|Yes| LOGIN["Log in"]
    REG --> LOGIN
    LOGIN --> HH{In a household?}
    HH -->|No| CREATE["Create household<br/>name, description, ID"]
    HH -->|Not yet| JOIN["Join by householdID"]
    HH -->|Yes| VIEW
    CREATE --> VIEW
    JOIN --> VIEW
    VIEW["View inventory<br/>pantry / fridge / freezer<br/>capacity, availability, freshness"]
    VIEW --> ACTION{Do what?}
    ACTION -->|Restock| RESTOCK["Add units with<br/>purchase + best-by date"]
    ACTION -->|Reserve| RESERVE["Claim units for yourself"]
    ACTION -->|Consume| CONSUME["Remove units, FIFO by batch"]
    ACTION -->|Release| RELEASE["Drop your own reservation"]
    RESTOCK --> VIEW
    RESERVE --> VIEW
    CONSUME --> VIEW
    RELEASE --> VIEW

    classDef plain fill:#ffffff,stroke:#8a8a8a,stroke-width:1px,color:#1a1a1a
    classDef gate fill:#f2f2f2,stroke:#8a8a8a,stroke-width:1px,color:#1a1a1a
    class START,REG,LOGIN,CREATE,JOIN,VIEW,RESTOCK,RESERVE,CONSUME,RELEASE plain
    class AUTH,HH,ACTION gate
```

Reserving is a heads-up to housemates, not a lock. It never blocks anyone else from consuming. Only the member who made a reservation can release it.
