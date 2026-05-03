function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("lab_user") || "null");
  } catch {
    localStorage.removeItem("lab_token");
    localStorage.removeItem("lab_user");
    return null;
  }
}

const state = {
  token: localStorage.getItem("lab_token"),
  user: readStoredUser(),
  templates: [],
  records: [],
  users: [],
  aiEnabled: false,
  editingTemplateId: null,
  editingUserId: null,
  pendingConfirmation: null,
};

if (!state.user) {
  state.token = null;
}

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function showToast(message) {
  const toast = $("#toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2800);
}

function setMessage(id, text, isError = false) {
  const element = $(id);
  element.textContent = text;
  element.classList.toggle("error", isError);
}

function clearSession(message = "") {
  state.token = null;
  state.user = null;
  localStorage.removeItem("lab_token");
  localStorage.removeItem("lab_user");
  renderAuthState();

  if (message) {
    setMessage("#loginMessage", message, true);
  }
}

function formatErrorDetail(detail, fallback) {
  if (Array.isArray(detail) && detail.length) {
    return detail.map((item) => item.msg || item.detail || String(item)).join(", ");
  }

  return detail || fallback;
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    if (contentType.includes("application/json")) {
      const body = await response.json();
      detail = formatErrorDetail(body.detail, detail);
    }

    if (response.status === 401) {
      clearSession("Session expired. Please sign in again.");
    }

    throw new Error(detail);
  }

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response;
}

async function downloadWithAuth(path, filename) {
  const response = await fetch(path, {
    headers: {
      Authorization: `Bearer ${state.token}`,
    },
  });

  if (!response.ok) {
    let detail = `Download failed (${response.status})`;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const body = await response.json();
      detail = formatErrorDetail(body.detail, detail);
    }

    if (response.status === 401) {
      clearSession("Session expired. Please sign in again.");
    }

    throw new Error(detail);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const data = await response.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function runAction(button, action, failureTarget = null) {
  const originalText = button?.textContent;
  if (button) {
    button.disabled = true;
    button.textContent = "Working...";
  }

  try {
    await action();
  } catch (error) {
    if (failureTarget) {
      setMessage(failureTarget, error.message, true);
    } else {
      showToast(error.message);
    }
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalText;
    }
  }
}

function can(role) {
  return state.user?.role === role;
}

function canEditTemplate(template) {
  return can("admin") || template.created_by_user_id === state.user?.id;
}

function isProtectedSuperAdmin(user) {
  const username = (user.username || "").trim().toLowerCase();
  const name = (user.name || "").trim().toLowerCase();
  return username === "supa admin" || username === "supa_admin" || name === "super admin";
}

function applyRoleVisibility() {
  $$("[data-admin]").forEach((el) => el.classList.toggle("hidden", !can("admin")));
  $$("[data-technician]").forEach((el) => el.classList.toggle("hidden", !can("technician")));
}

function showView(viewId) {
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === viewId));
  $$(".nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewId);
  });
}

function renderAuthState() {
  const isLoggedIn = Boolean(state.token && state.user);
  $("#loginView").classList.toggle("hidden", isLoggedIn);
  $("#appView").classList.toggle("hidden", !isLoggedIn);
  $("#loginPassword").value = "";

  if (isLoggedIn) {
    $("#currentUserName").textContent = state.user.name;
    $("#currentUserRole").textContent = state.user.role;
    applyRoleVisibility();
    $("#aiToggle").disabled = !can("admin");
  } else {
    $("#aiToggle").disabled = true;
  }
}

function renderDashboard() {
  $("#recordCount").textContent = state.records.length;
  $("#templateCount").textContent = state.templates.length;
  $("#aiStatus").textContent = state.aiEnabled ? "On" : "Off";
  $("#aiSettingText").textContent = state.aiEnabled ? "On" : "Off";
  $("#aiToggle").checked = state.aiEnabled;
}

function table(headers, rows) {
  if (!rows.length) {
    return "<p class=\"message\">No records found.</p>";
  }

  return `
    <table>
      <thead><tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr></thead>
      <tbody>${rows.join("")}</tbody>
    </table>
  `;
}

function renderTemplates() {
  $("#recordTemplate").innerHTML = state.templates
    .map((template) => `<option value="${template.id}">${template.name}</option>`)
    .join("");

  $("#templatesTable").innerHTML = table(
    ["ID", "Name", "Parameters", "Actions"],
    state.templates.map((template) => {
      const editButton = canEditTemplate(template)
        ? `<button class="secondary" data-edit-template-id="${template.id}" type="button">Edit</button>`
        : "";
      const deleteButton = can("admin")
        ? `<button class="danger" data-delete-template-id="${template.id}" type="button">Delete</button>`
        : "";

      return `
        <tr>
          <td>${template.id}</td>
          <td>${template.name}</td>
          <td>${template.parameters.map((p) => `${p.name} (${p.unit})`).join(", ")}</td>
          <td><div class="row-actions">${editButton}${deleteButton}</div></td>
        </tr>
      `;
    }),
  );

  renderResultInputs();
}

function renderResultInputs() {
  const templateId = Number($("#recordTemplate").value);
  const template = state.templates.find((item) => item.id === templateId);

  if (!template) {
    $("#resultInputs").innerHTML = "<p class=\"message\">Create a template first.</p>";
    return;
  }

  $("#resultInputs").innerHTML = template.parameters.map((parameter) => `
    <label>
      ${parameter.name} (${parameter.unit})
      <input type="number" step="any" data-result-name="${parameter.name}" required>
    </label>
  `).join("");
}

function renderRecords() {
  $("#recordsTable").innerHTML = table(
    ["Report", "Patient", "Test", "Date", "Actions"],
    state.records.map((record) => {
      const template = state.templates.find((item) => item.id === record.template_id);
      return `
        <tr>
          <td>${record.report_number || record.id}</td>
          <td>${record.patient_name}</td>
          <td>${template?.name || record.template_id}</td>
          <td>${record.created_at || "-"}</td>
          <td>
            <button class="secondary" data-pdf-id="${record.id}" type="button">PDF</button>
            <button class="secondary" data-summary-id="${record.id}" type="button">Summary</button>
          </td>
        </tr>
      `;
    }),
  );
}

function renderUsers(users) {
  state.users = users;
  $("#usersTable").innerHTML = table(
    ["ID", "Name", "Username", "Role", "Actions"],
    users.map((user) => `
      <tr>
        <td>${user.id}</td>
        <td>${user.name}</td>
        <td>${user.username}</td>
        <td>${user.role}</td>
        <td>
          <div class="row-actions">
            <button class="secondary" data-edit-user-id="${user.id}" type="button">Edit</button>
            <button
              class="danger"
              data-delete-user-id="${user.id}"
              type="button"
              ${isProtectedSuperAdmin(user) || user.id === state.user?.id ? "disabled" : ""}
            >Delete</button>
          </div>
        </td>
      </tr>
    `),
  );
}

function renderAudit(logs) {
  $("#auditTable").innerHTML = table(
    ["Time", "User", "Action", "Entity"],
    logs.map((log) => `
      <tr>
        <td>${log.created_at}</td>
        <td>${log.user_id || "-"}</td>
        <td>${log.action}</td>
        <td>${log.entity_type} ${log.entity_id || ""}</td>
      </tr>
    `),
  );
}

function addParameterRow(name = "", unit = "") {
  const row = document.createElement("div");
  row.className = "parameter-row";
  row.innerHTML = `
    <label>Parameter<input data-param-name value="${name}" required></label>
    <label>Unit<input data-param-unit value="${unit}" required></label>
    <button type="button" class="danger" data-remove-param>X</button>
  `;
  $("#templateParameters").appendChild(row);
}

function resetTemplateForm() {
  state.editingTemplateId = null;
  $("#templateForm").reset();
  $("#templateParameters").innerHTML = "";
  addParameterRow("Hemoglobin", "g/dL");
  $("#saveTemplateButton").textContent = "Save template";
  $("#cancelTemplateEditButton").classList.add("hidden");
  setMessage("#templateMessage", "");
}

function startTemplateEdit(templateId) {
  const template = state.templates.find((item) => item.id === templateId);
  if (!template) return;

  state.editingTemplateId = template.id;
  $("#templateName").value = template.name;
  $("#templateParameters").innerHTML = "";
  template.parameters.forEach((parameter) => {
    addParameterRow(parameter.name, parameter.unit);
  });
  $("#saveTemplateButton").textContent = "Save changes";
  $("#cancelTemplateEditButton").classList.remove("hidden");
  showView("templates");
}

function resetUserForm() {
  state.editingUserId = null;
  $("#userForm").reset();
  $("#userPassword").required = true;
  $("#userPassword").placeholder = "";
  $("#saveUserButton").textContent = "Create user";
  $("#cancelUserEditButton").classList.add("hidden");
  setMessage("#userMessage", "");
}

function startUserEdit(userId) {
  const user = state.users.find((item) => item.id === userId);
  if (!user) return;

  state.editingUserId = user.id;
  $("#userName").value = user.name;
  $("#userUsername").value = user.username;
  $("#userEmail").value = user.email;
  $("#userPassword").value = "";
  $("#userPassword").required = false;
  $("#userPassword").placeholder = "Leave blank to keep current password";
  $("#userRole").value = user.role;
  $("#saveUserButton").textContent = "Save changes";
  $("#cancelUserEditButton").classList.remove("hidden");
  showView("users");
}

function openConfirmation({ title, body, expectedText, onConfirm }) {
  state.pendingConfirmation = { expectedText, onConfirm };
  $("#confirmTitle").textContent = title;
  $("#confirmBody").textContent = body;
  $("#confirmInput").value = "";
  $("#confirmMessage").textContent = "";
  $("#confirmModal").classList.remove("hidden");
  $("#confirmInput").focus();
}

function closeConfirmation() {
  state.pendingConfirmation = null;
  $("#confirmModal").classList.add("hidden");
  $("#confirmInput").value = "";
  $("#confirmMessage").textContent = "";
}

async function loadHospital() {
  try {
    const hospital = await api("/hospital/profile");
    $("#labName").textContent = hospital.name;
    $("#hospitalName").value = hospital.name || "";
    $("#hospitalPhone").value = hospital.phone || "";
    $("#hospitalEmail").value = hospital.email || "";
    $("#hospitalRegistration").value = hospital.registration_number || "";
    $("#hospitalAddress").value = hospital.address || "";
  } catch {
    $("#labName").textContent = "Dashboard";
  }
}

async function loadAll() {
  if (!state.token) return;

  const [templates, records, aiSetting] = await Promise.all([
    api("/templates/"),
    api("/records/"),
    api("/settings/ai-summary"),
  ]);

  state.templates = templates;
  state.records = records;
  state.aiEnabled = aiSetting.enabled;

  await loadHospital();
  renderDashboard();
  renderTemplates();
  renderRecords();

  if (can("admin")) {
    const [users, auditLogs] = await Promise.all([
      api("/users/"),
      api("/audit-logs/"),
    ]);
    renderUsers(users);
    renderAudit(auditLogs);
  }
}

$("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#loginMessage", "");

  await runAction(event.submitter, async () => {
    const result = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: $("#loginUsername").value,
        password: $("#loginPassword").value,
      }),
    });

    state.token = result.access_token;
    state.user = result.user;
    localStorage.setItem("lab_token", state.token);
    localStorage.setItem("lab_user", JSON.stringify(state.user));
    renderAuthState();
    await loadAll();
  }, "#loginMessage");
});

$("#logoutButton").addEventListener("click", () => {
  clearSession();
});

$$(".nav button").forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.view));
});

$("#refreshButton").addEventListener("click", async (event) => {
  await runAction(event.currentTarget, async () => {
    await loadAll();
    showToast("Dashboard refreshed");
  });
});

$("#recordTemplate").addEventListener("change", renderResultInputs);

$("#recordForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#recordMessage", "");

  const results = {};
  $$("[data-result-name]").forEach((input) => {
    results[input.dataset.resultName] = Number(input.value);
  });

  await runAction(event.submitter, async () => {
    await api("/records/", {
      method: "POST",
      body: JSON.stringify({
        template_id: Number($("#recordTemplate").value),
        patient_name: $("#patientName").value,
        patient_age: Number($("#patientAge").value),
        patient_gender: $("#patientGender").value,
        patient_phone: $("#patientPhone").value || null,
        referring_doctor: $("#referringDoctor").value || null,
        results,
      }),
    });
    event.target.reset();
    await loadAll();
    setMessage("#recordMessage", "Report created.");
  }, "#recordMessage");
});

$("#recordsTable").addEventListener("click", async (event) => {
  const pdfId = event.target.dataset.pdfId;
  const summaryId = event.target.dataset.summaryId;

  if (pdfId) {
    try {
      await downloadWithAuth(`/records/${pdfId}/pdf`, `report_${pdfId}.pdf`);
    } catch (error) {
      showToast(error.message);
    }
  }

  if (summaryId) {
    try {
      const result = await api(`/records/${summaryId}/summary`);
      showToast(`${result.source}: ${result.summary.slice(0, 180)}`);
    } catch (error) {
      showToast(error.message);
    }
  }
});

$("#addParameterButton").addEventListener("click", () => addParameterRow());

$("#templateParameters").addEventListener("click", (event) => {
  if (event.target.dataset.removeParam !== undefined) {
    event.target.closest(".parameter-row").remove();
  }
});

$("#templatesTable").addEventListener("click", (event) => {
  const editTemplateId = Number(event.target.dataset.editTemplateId);
  const deleteTemplateId = Number(event.target.dataset.deleteTemplateId);

  if (editTemplateId) {
    startTemplateEdit(editTemplateId);
  }

  if (deleteTemplateId) {
    const template = state.templates.find((item) => item.id === deleteTemplateId);
    openConfirmation({
      title: "Delete template",
      body: `This will delete template "${template?.name || deleteTemplateId}" if no reports use it. Type DELETE TEMPLATE to continue.`,
      expectedText: "DELETE TEMPLATE",
      onConfirm: async () => {
        await api(`/templates/${deleteTemplateId}?confirm_text=${encodeURIComponent("DELETE TEMPLATE")}`, {
          method: "DELETE",
        });
        await loadAll();
        showToast("Template deleted.");
      },
    });
  }
});

$("#cancelTemplateEditButton").addEventListener("click", resetTemplateForm);

$("#templateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#templateMessage", "");

  const parameters = $$(".parameter-row").map((row) => ({
    name: row.querySelector("[data-param-name]").value,
    unit: row.querySelector("[data-param-unit]").value,
  }));

  await runAction(event.submitter, async () => {
    const isEditing = Boolean(state.editingTemplateId);
    await api(isEditing ? `/templates/${state.editingTemplateId}` : "/templates/", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify({
        name: $("#templateName").value,
        parameters,
      }),
    });
    resetTemplateForm();
    await loadAll();
    setMessage("#templateMessage", isEditing ? "Template updated." : "Template saved.");
  }, "#templateMessage");
});

$("#usersTable").addEventListener("click", (event) => {
  const editUserId = Number(event.target.dataset.editUserId);
  const deleteUserId = Number(event.target.dataset.deleteUserId);

  if (editUserId) {
    startUserEdit(editUserId);
  }

  if (deleteUserId) {
    const user = state.users.find((item) => item.id === deleteUserId);
    openConfirmation({
      title: "Delete user",
      body: `This will delete user "${user?.username || deleteUserId}". Type DELETE USER to continue.`,
      expectedText: "DELETE USER",
      onConfirm: async () => {
        await api(`/users/${deleteUserId}?confirm_text=${encodeURIComponent("DELETE USER")}`, {
          method: "DELETE",
        });
        await loadAll();
        showToast("User deleted.");
      },
    });
  }
});

$("#cancelUserEditButton").addEventListener("click", resetUserForm);

$("#userForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#userMessage", "");

  await runAction(event.submitter, async () => {
    const isEditing = Boolean(state.editingUserId);
    const payload = {
      name: $("#userName").value,
      username: $("#userUsername").value,
      email: $("#userEmail").value,
      role: $("#userRole").value,
    };

    if (!isEditing || $("#userPassword").value) {
      payload.password = $("#userPassword").value;
    }

    await api(isEditing ? `/users/${state.editingUserId}` : "/users/", {
      method: isEditing ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    resetUserForm();
    await loadAll();
    setMessage("#userMessage", isEditing ? "User updated." : "User created.");
  }, "#userMessage");
});

$("#hospitalForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  setMessage("#hospitalMessage", "");

  await runAction(event.submitter, async () => {
    await api("/hospital/profile", {
      method: "PUT",
      body: JSON.stringify({
        name: $("#hospitalName").value,
        address: $("#hospitalAddress").value || null,
        phone: $("#hospitalPhone").value || null,
        email: $("#hospitalEmail").value || null,
        registration_number: $("#hospitalRegistration").value || null,
      }),
    });
    await loadAll();
    setMessage("#hospitalMessage", "Hospital profile saved.");
  }, "#hospitalMessage");
});

$("#aiToggle").addEventListener("change", async (event) => {
  try {
    const result = await api("/settings/ai-summary", {
      method: "PUT",
      body: JSON.stringify({ enabled: event.target.checked }),
    });
    state.aiEnabled = result.enabled;
    renderDashboard();
    showToast(`AI generated description ${result.enabled ? "enabled" : "disabled"}`);
  } catch (error) {
    event.target.checked = state.aiEnabled;
    showToast(error.message);
  }
});

$("#exportRecordsButton").addEventListener("click", (event) => {
  runAction(event.currentTarget, async () => {
    await downloadWithAuth("/exports/records", "records_export.json");
    showToast("Records exported.");
  });
});

$("#exportDatabaseButton").addEventListener("click", (event) => {
  runAction(event.currentTarget, async () => {
    await downloadWithAuth("/exports/database", "lab_reports_backup.db");
    showToast("Database backup downloaded.");
  });
});

$("#cancelConfirmButton").addEventListener("click", closeConfirmation);

$("#confirmActionButton").addEventListener("click", async (event) => {
  if (!state.pendingConfirmation) return;

  if ($("#confirmInput").value !== state.pendingConfirmation.expectedText) {
    setMessage("#confirmMessage", "Confirmation text does not match.", true);
    return;
  }

  await runAction(event.currentTarget, async () => {
    await state.pendingConfirmation.onConfirm();
    closeConfirmation();
  }, "#confirmMessage");
});

addParameterRow("Hemoglobin", "g/dL");
renderAuthState();
if (state.token) {
  loadAll().catch((error) => {
    showToast(error.message);
  });
}
