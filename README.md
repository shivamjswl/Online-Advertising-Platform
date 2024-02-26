# Online-Advertising-Platform

This repository encompasses the implementation of an Online Advertising Platform, featuring diverse elements for orchestrating ad campaigns, presenting ads to users, amassing feedback, and crafting billing reports.

## Components

### Campaign Manager Interface
Empowering campaign managers to initiate and conclude ad campaigns by broadcasting ad instructions to a Kafka queue, the Campaign Manager Interface stands as a pivotal module.

### Ad Manager
Executing messages from the Kafka queue, the Ad Manager module synchronizes the MySQL store, steering the comprehensive life cycle of ad campaigns.

### Ad Server
Conducting auctions for showcasing ads on user devices, the Ad Server identifies the triumphant ad and bills the second-highest bid amount.

### User Simulator
Interacting with the Ad Server API, the User Simulator module emulates user actions by requesting and displaying ads.

### Feedback Handler
Acquiring user interaction feedback from the User Simulator, the Feedback Handler publishes it to another Kafka queue. Additionally, it updates the remaining budget for the ad campaign in MySQL.

### User Feedback Writer
Reading feedback events from the Kafka queue, the User Feedback Writer compiles them in HIVE, serving billing and archival purposes.

### Report Generator
Formulating a bill report for all ads exhibited during the system's runtime, the Report Generator concludes the ensemble.

## Tools Utilized

- Kafka: Employed for message queuing and event-driven communication amongst modules.
- MySQL: Serving as the repository for ad campaign data, it undergoes updates based on received instructions.
- HIVE: Utilized for storing and archiving user feedback events, catering to billing requirements.
- API: Offering interfaces for communication across modules (e.g., Campaign Manager Interface, Ad Server API, Feedback API).

## Challenges Overcome

In navigating the implementation of this Ad Campaign Management System, we confronted several challenges:

1. Integration Complexity: Merging diverse modules and ensuring seamless communication necessitated meticulous planning and coordination.
2. Real-time Data Processing: Effectively managing real-time ad requests, feedback aggregation, and updates to the campaign budget in MySQL demanded efficient data processing and synchronization.
3. Scalability and Performance: Certifying the system's capability to handle a substantial volume of ad requests, feedback events, and database updates while preserving performance and responsiveness presented a noteworthy challenge.
4. Billing and Reporting: Crafting the billing and reporting functionality to precisely calculate costs based on ad auctions and user interactions required careful contemplation of various factors.

These challenges were surmounted through extensive testing, performance optimization, and continual monitoring, securing the reliability and efficacy of the system.

## Conclusion

The Ad Campaign Management System delineated in this repository delivers a holistic solution for overseeing ad campaigns, showcasing ads to users, accumulating feedback, and composing billing reports. The strategic integration of diverse modules and tools facilitates efficient ad campaign management and in-depth analysis.
