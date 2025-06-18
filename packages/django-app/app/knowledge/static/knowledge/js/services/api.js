// API Service for Knowledge Base App
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
    // Detect user's timezone
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

    const data = await this.request("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password, timezone }),
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

  async createPage(title, content, slug, isPublished = true) {
    return await this.request("/knowledge/api/pages/", {
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
    return await this.request("/knowledge/api/pages/update/", {
      method: "PUT",
      body: JSON.stringify({
        page_id: pageId,
        ...updates,
      }),
    });
  }

  async deletePage(pageId) {
    return await this.request("/knowledge/api/pages/delete/", {
      method: "DELETE",
      body: JSON.stringify({ page_id: pageId }),
    });
  }

  async getPages(publishedOnly = true, limit = 10, offset = 0) {
    return await this.request(
      `/knowledge/api/pages/list/?published_only=${publishedOnly}&limit=${limit}&offset=${offset}`
    );
  }

  // New block-centric methods
  async getPageWithBlocks(pageId = null, date = null) {
    let params = "";
    if (pageId) {
      params = `?page_id=${pageId}`;
    } else if (date) {
      params = `?date=${date}`;
    }

    return await this.request(`/knowledge/api/page/${params}`);
  }

  async createBlock(blockData) {
    return await this.request("/knowledge/api/blocks/", {
      method: "POST",
      body: JSON.stringify(blockData),
    });
  }

  async updateBlock(blockData) {
    return await this.request("/knowledge/api/blocks/update/", {
      method: "PUT",
      body: JSON.stringify(blockData),
    });
  }

  async deleteBlock(blockData) {
    return await this.request("/knowledge/api/blocks/delete/", {
      method: "DELETE",
      body: JSON.stringify(blockData),
    });
  }

  async toggleBlockTodo(blockId) {
    return await this.request("/knowledge/api/blocks/toggle-todo/", {
      method: "POST",
      body: JSON.stringify({ block_id: blockId }),
    });
  }

  async getHistoricalData(daysBack = 30, limit = 50) {
    return await this.request(
      `/knowledge/api/historical/?days_back=${daysBack}&limit=${limit}`
    );
  }

  async getTagContent(tagName) {
    return await this.request(`/knowledge/api/tag/${encodeURIComponent(tagName)}/`);
  }

  // Legacy method for backward compatibility
  async getDailyNote(date) {
    return await this.getPageWithBlocks(null, date);
  }

  // Utility methods
  isAuthenticated() {
    return !!this.token;
  }

  getCurrentUser() {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  }

  // Timezone detection and management
  getCurrentBrowserTimezone() {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (error) {
      console.warn("Could not detect timezone:", error);
      return "UTC";
    }
  }

  checkTimezoneChange() {
    const currentUser = this.getCurrentUser();
    if (!currentUser || !currentUser.timezone) {
      return false;
    }

    const browserTimezone = this.getCurrentBrowserTimezone();
    const storedTimezone = currentUser.timezone;

    return browserTimezone !== storedTimezone;
  }

  async updateUserTimezone(newTimezone) {
    try {
      const result = await this.request("/api/auth/update-timezone/", {
        method: "POST",
        body: JSON.stringify({ timezone: newTimezone }),
      });

      if (result.success) {
        // Update local storage
        const currentUser = this.getCurrentUser();
        if (currentUser) {
          currentUser.timezone = newTimezone;
          localStorage.setItem("user", JSON.stringify(currentUser));
        }
      }

      return result;
    } catch (error) {
      console.error("Failed to update timezone:", error);
      throw error;
    }
  }
}

// Export for use in other files
window.apiService = new ApiService();
