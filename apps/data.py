from __future__ import annotations

PROJECTS: dict[str, dict] = {
    "gatekeeper": {
        "active": True,
        "title": "GateKeeper",
        "subtitle": "Access code auth gate for web apps",
        "description": [
            "A single sign-on system that protects a family of web apps behind one shared access code. Visitors prove access once by entering a code on the login page, and GateKeeper signs them in across every subdomain of the same domain: the portfolio, staff portals, the solver, and any future app. No user accounts, no per-app passwords, no hardcoded domains anywhere in the stack.",
            "An admin panel issues and revokes codes, with a backup code so the owner is never locked out. The access cookie is tamper-evident and every check validates it against the live database, so a code revoked in the panel is a hard kill switch across every protected app.",
        ],
        "tech": {
            "web": ["FastAPI", "Granian", "SQLAlchemy", "MySQL 8.4", "Docker", "Caddy", "PyJWT", "Cloudflare Tunnel"],
        },
        "features": [
            "Access code authentication with signed cookies",
            "Forward-auth session verification via Caddy",
            "Cross-subdomain cookie for shared auth across apps",
            "DB-driven routing and rule-group dispatch",
            "Admin panel to create and revoke access codes",
            "Backup code fallback for emergency access",
            "Audit logging and warning detection",
        ],
        "status": "operational",
        "reason": (
            "The moment a domain goes live, bots start crawling it, scraping "
            "whatever they can and probing for unsecured endpoints. GateKeeper is the "
            "boundary: anyone with a proper link gets in, anyone browsing directly "
            "gets a login page. One access code, one signed cookie, one redirect: "
            "security through a simple, verifiable boundary instead of a sprawling "
            "auth system."
        ),
        "url": "https://gatekeeper.projectnova.download/",
        "github": "https://github.com/NovaProtocol/GateKeeper",
        "links": [
            {
                "name": "Documentation",
                "url": "https://gatekeeper.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
    "portfolio": {
        "active": True,
        "title": "Portfolio",
        "subtitle": "Personal portfolio site",
        "description": [
            "This site. A FastAPI portfolio documenting every project in the stack, each with a detail page, tech tags, a live-site embed with online/offline status, and key features. Served by Granian (ASGI, 1 worker) in a Docker container, exposed through a Cloudflare tunnel and Caddy, with RequestID + SecurityHeaders middleware and structured errors.",
            "It doubles as the integration test for the rest of the ecosystem: protected by GateKeeper, so unauthenticated visitors are redirected to log in and sent back with a verified session, and project pages embed the other live apps directly, so you can solve problems in the sandbox, browse bills, or manage access codes without leaving the page.",
        ],
        "tech": {
            "web": ["FastAPI", "Granian", "Jinja2", "Docker", "Caddy", "Cloudflare Tunnel"],
        },
        "features": [
            "Project showcase with detail pages and tech tags",
            "GateKeeper integration for access control (wildcard gate)",
            "RequestIDMiddleware + structlog JSON + {error:{code,message,request_id}} envelope",
        ],
        "status": "operational",
        "reason": (
            "This site is the front door to everything else, and the proof that "
            "everything behind it actually works: real domains routed through "
            "Cloudflare Tunnel without needing a public IP, containers wired securely "
            "inside Docker networks, and a GateKeeper-protected stack running in "
            "production."
        ),
        "url": "https://portfolio.projectnova.download/",
        "github": "https://github.com/NovaProtocol/Portfolio",
        "links": [
            {
                "name": "Documentation",
                "url": "https://portfolio.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
    "water-billing-system": {
        "active": True,
        "title": "Water Billing System",
        "subtitle": "Cotta Realty & Development Corporation",
        "description": [
            "A Utility CIS (Customer Information System) for water billing, built for Cotta Realty & Development Corporation and used by tenants across their subdivisions in Quezon, Philippines. It runs the whole cycle in one platform: meter reading, bill generation, payments, and receipts, with dedicated portals for tenants, meter readers, and the billing office.",
            "Meter readers carry a React Native app that works offline. Each meter has an NFC tag, and readers tap the meter to open the customer record, enter the reading, and the app queues everything on the phone until connectivity returns. The tag's security key derives on-device from the chip's factory ID, so it never crosses the network, and the system catches tampered or duplicated tags.",
            "Readings generate bills automatically against a five-tier progressive tariff with late penalties. Tenants pay through 22 methods: GCash, Maya, cards, bank debits, over-the-counter, and QRPh. The platform reconciles every payment with the gateway automatically, so the billing office doesn't settle transactions by hand. A waterfall rule applies money to the oldest unpaid bill first, carries overpayments forward as credit, and lets one receipt cover several bills.",
            "The platform runs as 11 Docker containers with the API sealed off from the public internet. The API and portals are async FastAPI services on Granian, built for throughput, and each role only reaches the part of the API it needs. On startup, the system audits its own database schema against the code and repairs drift automatically, so it stays healthy between deployments.",
            "Project Note: this is a live demo of the full system, hosted on a low-end server to stay affordable. The live site shows the features, not the real performance headroom. You can log in with the given demo credentials and explore.",
        ],
        "tech": {
            "web": [
                "FastAPI",
                "SQLAlchemy",
                "MySQL 8.4",
                "Caddy",
                "Granian",
                "Xendit API",
                "Cloudflare Tunnel",
                "Docker",
            ],
            "mobile": ["React Native", "Expo", "TypeScript", "NFC (NTAG215)", "SQLite"],
        },
        "features": [
            "Async FastAPI API and portals on Granian, built for throughput under load",
            "Role-scoped API: each portal and app only reaches the endpoints its users need",
            "Offline-first React Native meter reading app with tamper-proof NFC meter tags",
            "22 payment methods via Xendit, with automatic reconciliation and reversal handling",
            "Automatic billing from a 5-tier progressive tariff with late penalties and waterfall payments",
            "11 Docker containers across 6 isolated networks, API unreachable from the public internet",
            "Startup database self-heal: schema audited against the code, drift fixed automatically",
            "Strict environment validation: the system refuses to boot with missing required settings",
            "4 authentication layers for staff, tenants, internal services, and GateKeeper SSO",
            "Full technical documentation with API reference (MkDocs)",
        ],
        "status": "operational",
        "note": "Update: Did not get hired",
        "reason": (
            "Utility billing handles some of the most sensitive data there is: "
            "customer identities, meter records, payments. This project proves I can "
            "build that properly: customer data sealed in internal networks, granular "
            "staff permissions, signed sessions, a full audit trail, and payment "
            "reconciliation that can be traced end to end."
        ),
        "url": "https://water-billing-system.projectnova.download/",
        "github": "https://github.com/NovaProtocol/WaterBillingSystem",
        "image": "assets/images/water-billing-system/water-billing-system-preview.png",
        "links": [
            {
                "name": "Staff Site",
                "url": "https://water-billing-system.projectnova.download/staff/",
                "icon": "fas fa-user-tie",
            },
            {
                "name": "Dev Site",
                "url": "https://water-billing-system.projectnova.download/developer/",
                "icon": "fas fa-code-branch",
            },
            {
                "name": "Documentation",
                "url": "https://water-billing-system.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
            {
                "name": "phpMyAdmin",
                "url": "https://water-billing-system.projectnova.download/phpmyadmin/",
                "icon": "fas fa-database",
            },
        ],
        "testing": {
            "staff": {
                "username": "superuser",
                "password": "superuser",
            },
            "customer": {
                "account_number": "1 to 10000",
                "registered_name": "Not needed (DEBUG mode)",
                "last_receipt_number": "Not needed (DEBUG mode)",
            },
        },
        "buttons": [],
    },
    "mle-review": {
        "active": True,
        "title": "MELE Review",
        "subtitle": "Board exam reviewer — Mechanical Engineering Licensure Exam",
        "description": [
            "A self-hosted practice site for the Mechanical Engineering Licensure Exam. Upload past-board-exam PDFs as question sources, and the platform turns them into a searchable question bank: filter by answered/unanswered/flagged, search across question text and choices, reveal the correct answer with green/red feedback, and flag questions for review.",
            "Each question carries a notebook-style solution editor. Build solutions from blocks: constants with unit autosuggestion, MathQuill formula blocks, and answer blocks. Hitting Run evaluates the formulas top-to-bottom with a unit-aware solver, auto-solves single-variable equations by binary search, and normalizes metric/English conventions. Solutions persist per question and render read-only for anyone, while a write-access password lets the owner edit and upload.",
        ],
        "tech": {
            "web": [
                "FastAPI",
                "Granian",
                "SQLAlchemy",
                "MySQL 8.4",
                "Caddy",
                "Docker",
                "Cloudflare Tunnel",
                "itsdangerous",
            ],
            "lib": ["MathQuill", "math.js"],
        },
        "features": [
            "PDF question sources with per-question banks, search, filter, and pagination",
            "Answer reveal with green/red feedback and flag-for-review",
            "Notebook-style solution editor: constants, formula blocks, and answer blocks",
            "Unit-aware solver with unit autosuggestion, binary-search solving, and metric/English conventions",
            "Read-only solution view for everyone; password-protected write mode for editing",
            "GateKeeper-protected access behind a Cloudflare tunnel",
        ],
        "status": "in progress",
        "reason": (
            "The MELE board exam is make-or-break, and past papers deserve a "
            "better practice tool than a stack of PDFs. This project turns those "
            "papers into a searchable question bank and proves I can build a "
            "browser-based math solver that handles real engineering equations "
            "with units, not just toy examples."
        ),
        "url": "https://melereview.projectnova.download/",
        "github": "https://github.com/NovaProtocol/MELEReviewSite",
        "links": [
            {
                "name": "Documentation",
                "url": "https://melereview.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
    "solvespace": {
        "active": True,
        "title": "SolveSpace",
        "subtitle": "Self-hosted Python practice sandbox",
        "description": [
            "A self-hosted platform for practicing Python programming problems. Browse a problem library with images and tags, track progress per problem, and submit solutions in the browser. Problems and submissions live in MySQL, and a separate executor container runs every submission in isolation.",
            "Each submission executes in its own hardened sandbox: no network access, a read-only filesystem, no secrets inherited from the host, and hard memory, CPU, and process limits enforced on the whole process tree. If the sandbox fails to start, the submission is marked failed rather than ever running unsandboxed.",
            "I built it to learn process isolation and sandboxing. It served that purpose well, and it's not actively used anymore.",
        ],
        "status": "halted",
        "status_reason": "Lack of Productive Use: it's cool, but there are over 100 LeetCode clones that function way better.",
        "reason": (
            "Built to learn what it actually takes to run untrusted code safely: "
            "namespaces, resource limits, and process isolation. The sandboxing "
            "worked exactly as intended; the use case just didn't outlive the "
            "learning."
        ),
        "tech": {
            "web": ["Flask", "Gunicorn", "MySQL 8.4", "Docker", "Bubblewrap", "Cloudflare Tunnel"],
        },
        "features": [
            "Problem library with images, tags, and hidden judge test cases",
            "Sandboxed solution judging via bubblewrap with hard rlimits (1GB memory, 25s CPU, 64 processes)",
            "Background execution queue in MySQL, polled by a dedicated executor container",
            "GateKeeper-protected frontend with per-problem progress tracking",
            "phpMyAdmin for database management",
        ],
        "url": "https://solver.projectnova.download/",
        "github": "https://github.com/NovaProtocol/SolveSpace",
        "links": [
            {
                "name": "Documentation",
                "url": "https://solver.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
    "buddys-freelance-project": {
        "active": False,
        "title": "Buddy's Website",
        "subtitle": "Freelance: Buddy's Restaurant",
        "description": [
            "A marketing site for Buddy's, a Pahiyas festival-inspired Filipino restaurant chain founded in Lucban, Quezon, in 1985. The site brings a local food institution online: a full menu with real pricing, a directory of branches across Quezon, Metro Manila, Laguna, and Batangas, private event details, and a product page for every dish.",
            "Prices live in a single pricing dataset, and a curated alias layer bridges naming differences between the menu and the pricing data so every dish shows the right amount. Branch pages carry addresses, operating hours, phone numbers, map links, and photo galleries. Product pages pull descriptive copy, related items, and size options automatically from the pricing data.",
        ],
        "tech": {
            "web": ["FastAPI", "Granian", "Jinja2", "Docker", "Caddy", "Cloudflare Tunnel"],
        },
        "features": [
            "Full menu and product pages generated from unified pricing data",
            "Curated price-alias layer so every menu item shows the right price",
            "Branch directory with locations, hours, phone numbers, maps, and photo galleries",
            "Private events page with event listings",
            "GateKeeper-protected frontend served behind a Cloudflare tunnel",
        ],
        "status": "operational",
        "reason": (
            "Above all, this was a learning playground. I used Buddy's, a real local "
            "business, as the subject to teach myself modern frontend techniques: "
            "animated CSS, scroll-triggered reveals, hover micro-interactions, glass "
            "morphism, and the Pahiyas festival-inspired theming that gives the site "
            "its character. Along the way I also turned a physical menu into a "
            "maintainable system with content-driven pages and a single source of "
            "truth for pricing, all served through a FastAPI site behind the same "
            "hardened Docker and GateKeeper setup as the rest of my stack."
        ),
        "url": "https://buddys.projectnova.download/",
        "github": "https://github.com/NovaProtocol/BuddysFreelanceProject",
        "links": [
            {
                "name": "Documentation",
                "url": "https://buddys.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
    # intentionally public — SVG embeds (GitHub has no cookie jar, gate would break)
    "novaprotocol": {
        "active": True,
        "title": "NovaProtocol",
        "title_prefix": "https://github.com/",
        "subtitle": "Dynamic GitHub profile asset server",
        "description": [
            "A public asset server that produces the dynamic SVG badges and animations embedded in my GitHub profile README. Visit my profile and every graphic you see -- the name badge, skills list, and the animated console session -- is a live SVG served by this app, rendered fresh on every page load.",
            "Each endpoint generates hand-crafted SVG output from custom Python utilities. The console session simulates a boot-up sequence with typing effects, per-line scroll, and color-coded output. Skills badges render multi-color blocks at proportional widths. The name badge combines typography and layout into a single formatted SVG header.",
            "It is intentionally public with no authentication layer: GitHub loads these images as embedded content, and embedders have no cookie jar, so a GateKeeper forward-auth gate would break the very thing the project was built for. The stack stays deliberately small -- one FastAPI app, one Caddy proxy, one container.",
        ],
        "tech": {
            "web": ["FastAPI", "Granian", "Caddy", "Docker", "Cloudflare Tunnel"],
            "lib": ["svgwrite"],
        },
        "features": [
            "Hand-crafted SVG generation with no templates -- every badge is pure Python output",
            "Animated console session with typing effects, scrolling, and color-coded terminal output",
            "Multi-color skills badges with padded blocks and percentage-based progress bars",
            "Intentionally public (no auth gate) since GitHub embedders have no session",
            "Test suite covering route cache headers, SVG structure, and edge cases",
        ],
        "status": "operational",
        "reason": (
            "GitHub profile pages are static by default. NovaProtocol turns mine "
            "into a live window: the SVG endpoints regenerate on every request, so I "
            "can update my skills, add new badges, or change the console animation "
            "without touching the README. It is the only intentionally public service "
            "in my stack, and the one visitors see first -- before they even know the "
            "rest of the ecosystem exists."
        ),
        "url": "https://github.projectnova.download/test",
        "github": "https://github.com/NovaProtocol/NovaProtocol",
        "links": [
            {
                "name": "Documentation",
                "url": "https://github.projectnova.download/documentation/",
                "icon": "fas fa-book",
            },
        ],
        "buttons": [],
    },
}
