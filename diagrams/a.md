flowchart LR
    subgraph Client
        A([Client])
    end

    subgraph "Application Layer"
        
        subgraph "Web Server"
        B([Uvicorn])
        end

        subgraph "Routing Logic | main.py"
            C1{{Endpoints}}
        end

        subgraph "Pydantic Models | /schemas"
            D1[User]
        end

        subgraph "ORM Models| /models"
            E1[User]
        end

        subgraph "ORM Session | /database"
            F1([Engine])
            F2[[ORM Base Class]]
            F3[(Connection Generator)]
        end

    end

    subgraph Database
        G[(MySQL)]
    end

    subgraph "UI"
        H[/JavaScript/]
        I[/HTML/]
    end

    A -->|http://localhost:8000<br>GET/POST| B
    B -->|main.py| C1
    C1--> D1
    E1 --> F2
    F3 -->|async SQLAlchemy| G
    C1 --> E1
    C1 --> F1
    C1 --> F3
    H & I --> A
