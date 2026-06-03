# GameHub - Online Gaming Website

A full-featured Python Flask website for playing games online with user authentication, game categories, and user profiles.

## Features

✨ **User System**
- User registration and login with password hashing
- User profiles with game statistics
- Session management

🎮 **Games**
- Browse featured games on homepage
- Play individual games
- Organize games by categories
- Search functionality

📊 **Categories**
- Action, Puzzle, Adventure, and Strategy games
- Browse all games in a category
- Sample games included

## Installation (for manual use)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5000`

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── games.db              # SQLite database (created on first run)
├── static/
│   └── style.css         # CSS styling
├── template/
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Homepage
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── game.html         # Individual game page
│   ├── category.html     # Category page
│   ├── search.html       # Search results page
│   └── profile.html      # User profile page
└── games/                # All Game Files
    ├── uno.py
    ├── tetris.py
    ├── chess_online.py
    ├── drago_quest.py
    ├── memory_match.py
    ├── snake.py
    ├── space_invaders.py
    └── tic_tac_toe
```

## Routes

- **`/`** - Homepage with featured games and categories
- **`/<gamename>`** - Individual game page
- **`/category/<categoryname>`** - View games in a category
- **`/search`** - Search for games
- **`/user/<username>`** - View user profile and scores
- **`/login`** - Login page
- **`/register`** - Registration page

## Database

The application uses SQLite with the following tables:
- `users` - User accounts
- `categories` - Game categories
- `games` - Game listings
- `user_scores` - Player scores and statistics

The database is automatically created on first run with sample data.

## Default Games

- Space Invaders (Action)
- Tetris (Puzzle)
- Chess Online (Strategy)
- Dragon Quest (Adventure)

## Adding New Games

You can suggest new games in the Issues page of github, or modify the files and upload the new game files to you suggestion.

## Notes

- The secret key should be changed for production use
- Passwords are hashed using Werkzeug's security functions
- The app runs in debug mode by default (change for production)
- Images use placeholder URLs - replace with actual game images
- Not all Games are perfect and sometimes they don't work

## Future Enhancements

- Multiplayer support
- Social features (friends, chat)
