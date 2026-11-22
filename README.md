# CutieHack2026
Cutie Hack hackathon project 2026


'''classDiagram


    class User {
        +String id
        +String displayName
        +String profilePhotoUrl
        +int score
    }
    class Sighting {
        +String id
        +String userId
        +String photoUrl
        +DateTime capturedAt
        +DateTime submittedAt
        +float latitude
        +float longitude
        +float gpsAccuracy
        +int groupSize
        +String behavior
        +int pointsEarned
    }
    class BurroWatchService {
        +login() Optional~User~
        +getProfile(String userId) Optional~User~
        +submitSighting(Sighting sighting, bytes photo) Sighting
        +getSightingHistory(String userId) List~Sighting~
        +getLeaderboard() List~User~
        +getMapSightings() List~Sighting~
        +exportCSV() String
    }
    
    User "1" --> "0..*" Sighting : submits
    BurroWatchService ..> User : reads and updates
    BurroWatchService ..> Sighting : saves and retrieves
    
    '''
