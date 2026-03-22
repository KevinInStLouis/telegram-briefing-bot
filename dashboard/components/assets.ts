export const ASSETS = {
  // Background
  BACKGROUND:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/8b501664-722e-4be8-cf71-83aab7756e00/public",

  // Stevens
  STEVENS_FRONT:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/8b8432bb-add2-44ad-bb12-44b8ea215500/public",
  STEVENS_BACK:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/e28da8ab-7710-4b82-8e32-8fdf65c2ed00/public",
  STEVENS_WALKING:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/bd7b9997-09b2-4b35-6eb9-9975a85bb700/public",

  // Mailman
  MAILMAN_STANDING:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/20a6493d-cc31-475e-aa83-ac97d317e400/public",
  MAILMAN_WALKING:
    "https://imagedelivery.net/iHX6Ovru0O7AjmyT5yZRoA/61604576-8a83-4d85-d5e4-8e8e26641700/public",
};

// Scene positions for characters and interactive elements
export const SCENE_POSITIONS = {
  // Stevens starts inside the house near the notebook
  STEVENS_DEFAULT: { x: 470, y: 600 },

  // Interactive elements
  NOTEBOOK: { x: 540, y: 690 }, // The open book on the table
  CALENDAR: { x: 392, y: 524 }, // Calendar on the wall
  MAILBOX: { x: 160, y: 580 }, // Mailbox outside
  TELEGRAPH: { x: 725, y: 580 }, // Telegraph on the desk
};

// Source types for different animations
export const SOURCE_TYPES = {
  CALENDAR: "calendar",
  MAIL: "usps",
  TELEGRAM: "telegram",
  WEATHER: "weather",
  DEFAULT: "default",
};

