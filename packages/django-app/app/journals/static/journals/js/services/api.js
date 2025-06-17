// API Service for Journal App
class ApiService {
  constructor() {
    this.baseURL = window.location.origin;
    this.token = localStorage.getItem("authToken");
  }

  // Get CSRF token from cookies
  getCsrfToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async request(url, options = {}) {
    const config = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    // Add CSRF token for non-GET requests
    if (options.method && options.method !== "GET") {
      const csrfToken = this.getCsrfToken();
      if (csrfToken) {
        config.headers["X-CSRFToken"] = csrfToken;
      }
    }

    if (this.token) {
      config.headers["Authorization"] = `Token ${this.token}`;
    }

    try {
      const response = await fetch(`${this.baseURL}${url}`, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.errors?.non_field_errors?.[0] || "Request failed"
        );
      }

      return data;
    } catch (error) {
      console.error("API Error:", error);
      throw error;
    }
  }

  // Auth methods
  async login(email, password) {
    const data = await this.request("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (data.success) {
      this.token = data.data.token;
      localStorage.setItem("authToken", this.token);
      localStorage.setItem("user", JSON.stringify(data.data.user));
    }

    return data;
  }

  async register(email, password) {
    const data = await this.request("/api/auth/register/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    if (data.success) {
      this.token = data.data.token;
      localStorage.setItem("authToken", this.token);
      localStorage.setItem("user", JSON.stringify(data.data.user));
    }

    return data;
  }

  async logout() {
    try {
      await this.request("/api/auth/logout/", { method: "POST" });
    } finally {
      this.token = null;
      localStorage.removeItem("authToken");
      localStorage.removeItem("user");
    }
  }

  async me() {
    return await this.request("/api/auth/me/");
  }

  // Journal methods
  async createOrUpdateEntry(entryDate, content) {
    return await this.request("/journals/api/entries/", {
      method: "POST",
      body: JSON.stringify({
        entry_date: entryDate,
        content: content,
      }),
    });
  }

  async getEntry(entryDate) {
    return await this.request(
      `/journals/api/entries/get/?entry_date=${entryDate}`
    );
  }

  async getEntries(limit = 10, offset = 0) {
    return await this.request(
      `/journals/api/entries/list/?limit=${limit}&offset=${offset}`
    );
  }

  async createPage(title, content, slug, isPublished = true) {
    return await this.request("/journals/api/pages/", {
      method: "POST",
      body: JSON.stringify({
        title,
        content,
        slug,
        is_published: isPublished,
      }),
    });
  }

  async updatePage(pageId, updates) {
    return await this.request("/journals/api/pages/update/", {
      method: "PUT",
      body: JSON.stringify({
        page_id: pageId,
        ...updates,
      }),
    });
  }

  async deletePage(pageId) {
    return await this.request("/journals/api/pages/delete/", {
      method: "DELETE",
      body: JSON.stringify({ page_id: pageId }),
    });
  }

  async getPages(publishedOnly = true, limit = 10, offset = 0) {
    return await this.request(
      `/journals/api/pages/list/?published_only=${publishedOnly}&limit=${limit}&offset=${offset}`
    );
  }

  // Utility methods
  isAuthenticated() {
    return !!this.token;
  }

  getCurrentUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  }
}

// Export for use in other files
window.apiService = new ApiService();
