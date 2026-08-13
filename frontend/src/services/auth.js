// Simple mock auth service using localStorage
const USERS_KEY = "ai_comparator_users";
const CURRENT_USER_KEY = "ai_comparator_current_user";

function getUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "{}");
  } catch {
    return {};
  }
}

export function registerUser(username, password) {
  const users = getUsers();
  if (users[username.toLowerCase()]) {
    throw new Error("Username already exists.");
  }
  users[username.toLowerCase()] = { username, password };
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
  // Auto login after registration
  return loginUser(username, password);
}

export function loginUser(username, password) {
  const users = getUsers();
  const user = users[username.toLowerCase()];
  if (!user || user.password !== password) {
    throw new Error("Invalid username or password.");
  }
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
  return user;
}

export function logoutUser() {
  localStorage.removeItem(CURRENT_USER_KEY);
}

export function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem(CURRENT_USER_KEY) || "null");
  } catch {
    return null;
  }
}
