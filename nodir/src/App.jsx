import { useEffect, useState } from "react";

import { api, getSession } from "./api.js";

const money = (value) =>
  `${Number(value || 0).toLocaleString("uz-UZ")} so‘m`;

const statusNames = {
  new: "Yangi",
  queued: "Navbatda",
  printing: "Chop etilmoqda",
  ready: "Tayyor",
  completed: "Topshirildi",
  cancelled: "Bekor qilindi",
};

function AuthPanel({ onLogin, onNotice }) {
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values = Object.fromEntries(form.entries());
    setBusy(true);
    try {
      if (mode === "register") {
        await api("/auth/register", {
          method: "POST",
          body: {
            fullName: values.fullName,
            username: values.username,
            email: values.email,
            password: values.password,
            confirm: values.confirm,
          },
        });
        onNotice("Ro‘yxatdan o‘tildi. Tizimga kirishingiz mumkin.", "success");
        setMode("login");
      } else {
        const result = await api("/auth/login", {
          method: "POST",
          body: { username: values.username, password: values.password },
        });
        onLogin(result.user);
      }
    } catch (error) {
      onNotice(error.message, "danger");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-layout">
      <section className="hero auth-hero">
        <div className="eyebrow mb-3">Raqamli chop etish xizmati</div>
        <h1>Navbatni kutmang.<br />Hujjatingiz tayyor bo‘lsin.</h1>
        <p className="mt-4 mb-0">
          PDF faylingizni yuboring, chop etish parametrlarini tanlang va
          buyurtmangizni olish kodi bilan olib keting.
        </p>
        <div className="auth-benefits">
          <span><i className="bi bi-cloud-arrow-up" /> PDF’ni onlayn yuboring</span>
          <span><i className="bi bi-calculator" /> Narxni oldindan biling</span>
          <span><i className="bi bi-ticket-perforated" /> Kod bilan tez olib keting</span>
        </div>
      </section>
      <section className="form-card auth-card">
        <div className="auth-switch">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => setMode("login")}
            type="button"
          >
            Kirish
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => setMode("register")}
            type="button"
          >
            Ro‘yxatdan o‘tish
          </button>
        </div>
        <h2>{mode === "login" ? "Xush kelibsiz" : "Hisob yarating"}</h2>
        <p className="muted">
          {mode === "login"
            ? "Davom etish uchun ma’lumotlaringizni kiriting."
            : "Yangi hisob orqali buyurtma berishni boshlang."}
        </p>
        <form onSubmit={submit}>
          {mode === "register" && (
            <label className="field">
              <span>F.I.Sh.</span>
              <input className="form-control" name="fullName" minLength="3" maxLength="120" required />
            </label>
          )}
          <label className="field">
            <span>{mode === "login" ? "Login yoki email" : "Foydalanuvchi nomi"}</span>
            <input
              className="form-control"
              name="username"
              autoComplete="username"
              minLength={mode === "register" ? 3 : undefined}
              required
            />
          </label>
          {mode === "register" && (
            <label className="field">
              <span>Email</span>
              <input className="form-control" name="email" type="email" maxLength="120" required />
            </label>
          )}
          <label className="field">
            <span>Parol</span>
            <input
              className="form-control"
              name="password"
              type="password"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={mode === "register" ? 8 : undefined}
              required
            />
          </label>
          {mode === "register" && (
            <label className="field">
              <span>Parolni tasdiqlang</span>
              <input
                className="form-control"
                name="confirm"
                type="password"
                autoComplete="new-password"
                minLength="8"
                required
              />
            </label>
          )}
          <button className="btn btn-primary w-100 mt-2" disabled={busy} type="submit">
            {busy ? "Kuting..." : mode === "login" ? "Kirish" : "Hisob yaratish"}
          </button>
        </form>
      </section>
    </div>
  );
}

function OrderTable({ orders, user, onDetails, onStatusChange }) {
  if (!orders.length) {
    return (
      <div className="empty-state">
        <i className="bi bi-inbox" />
        <h3>Hozircha buyurtmalar yo‘q</h3>
        <p className="muted mb-0">Yangi buyurtmalar shu yerda ko‘rinadi.</p>
      </div>
    );
  }

  return (
    <div className="table-responsive order-table">
      <table className="table align-middle">
        <thead>
          <tr>
            <th>Buyurtma</th>
            {user.role !== "student" && <th>Talaba</th>}
            <th>Holat</th>
            <th>Narx</th>
            <th>Sana</th>
            <th>Amallar</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td>
                <strong>{order.number}</strong>
                {order.urgent && <span className="urgent-tag ms-2">Shoshilinch</span>}
              </td>
              {user.role !== "student" && <td>{order.student.fullName}</td>}
              <td><span className={`status-pill status-${order.status}`}>{statusNames[order.status] || order.status}</span></td>
              <td>{money(order.totalPrice)}</td>
              <td>{new Date(order.createdAt).toLocaleDateString("uz-UZ")}</td>
              <td className="actions-cell">
                {user.role === "student" && (
                  <button className="btn btn-sm btn-outline-primary" onClick={() => onDetails(order.id)}>
                    Tafsilot
                  </button>
                )}
                {user.role === "operator" && ["new", "queued"].includes(order.status) && (
                  <button className="btn btn-sm btn-warning" onClick={() => onStatusChange(order.id, "printing")}>
                    Chop etish
                  </button>
                )}
                {user.role === "operator" && order.status === "printing" && (
                  <button className="btn btn-sm btn-success" onClick={() => onStatusChange(order.id, "ready")}>
                    Tayyor
                  </button>
                )}
                {user.role === "operator" && order.file && !order.file.deleted && (
                  <a className="btn btn-sm btn-outline-secondary" href={`/api/operator/orders/${order.id}/file`}>
                    <i className="bi bi-file-earmark-pdf me-1" /> PDF
                  </a>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NewOrder({ onCreated, onNotice }) {
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const data = new FormData(formElement);
    setBusy(true);
    try {
      const result = await api("/student/orders", { method: "POST", body: data });
      formElement.reset();
      onCreated(result);
    } catch (error) {
      onNotice(error.message, "danger");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="form-card content-card">
      <div className="eyebrow text-primary">Talaba xizmati</div>
      <h2>Yangi buyurtma</h2>
      <p className="muted">PDF va chop etish parametrlarini kiriting.</p>
      <form onSubmit={submit}>
        <label className="field">
          <span>PDF fayl</span>
          <input className="form-control" type="file" name="file" accept="application/pdf,.pdf" required />
        </label>
        <div className="form-grid three">
          <label className="field"><span>Birinchi bet</span><input className="form-control" type="number" name="pageFrom" min="1" defaultValue="1" required /></label>
          <label className="field"><span>Oxirgi bet</span><input className="form-control" type="number" name="pageTo" min="1" defaultValue="1" required /></label>
          <label className="field"><span>Nusxalar</span><input className="form-control" type="number" name="copies" min="1" max="100" defaultValue="1" required /></label>
        </div>
        <div className="form-grid three">
          <label className="field"><span>Rang</span><select className="form-select" name="colorMode"><option value="bw">Oq-qora</option><option value="color">Rangli</option></select></label>
          <label className="field"><span>Chop turi</span><select className="form-select" name="sideMode"><option value="single">Bir tomonlama</option><option value="double">Ikki tomonlama</option></select></label>
          <label className="field"><span>Muqova</span><select className="form-select" name="bindingType"><option value="none">Muqovasiz</option><option value="simple">Oddiy</option><option value="spiral">Spiral</option></select></label>
        </div>
        <label className="urgent-check"><input type="checkbox" name="urgent" /> Shoshilinch buyurtma</label>
        <button className="btn btn-primary mt-3" disabled={busy} type="submit">
          {busy ? "Buyurtma yaratilmoqda..." : "Buyurtmani yuborish"}
        </button>
      </form>
    </section>
  );
}

function PriceSettings({ prices, onSave, onNotice }) {
  async function submit(event) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const result = await api("/owner/prices", { method: "PUT", body: values });
      onSave(result.prices);
      onNotice("Narxlar saqlandi.", "success");
    } catch (error) {
      onNotice(error.message, "danger");
    }
  }

  const fields = [
    ["blackWhitePagePrice", "Oq-qora bet narxi"],
    ["colorPagePrice", "Rangli bet narxi"],
    ["simpleBindingPrice", "Oddiy muqova"],
    ["spiralBindingPrice", "Spiral muqova"],
    ["urgentPercentage", "Shoshilinch ustama (%)"],
    ["maxFileSizeMb", "Maksimal fayl hajmi (MB)"],
  ];

  return (
    <section className="form-card content-card">
      <div className="eyebrow text-primary">Boshqaruv</div>
      <h2>Narx sozlamalari</h2>
      <form onSubmit={submit}>
        <div className="form-grid two">
          {fields.map(([name, label]) => (
            <label className="field" key={name}>
              <span>{label}</span>
              <input
                className="form-control"
                name={name}
                type="number"
                min="0"
                step={name === "maxFileSizeMb" ? "1" : "0.01"}
                defaultValue={prices[name]}
                required
              />
            </label>
          ))}
        </div>
        <button className="btn btn-primary mt-3" type="submit">O‘zgarishlarni saqlash</button>
      </form>
    </section>
  );
}

function PickupForm({ onNotice, onComplete }) {
  async function submit(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const data = new FormData(formElement);
    try {
      const result = await api("/operator/pickup", {
        method: "POST",
        body: { code: data.get("code") },
      });
      formElement.reset();
      onComplete(result.order);
      onNotice(`${result.order.number} buyurtmasi topshirildi.`, "success");
    } catch (error) {
      onNotice(error.message, "danger");
    }
  }

  return (
    <section className="form-card content-card pickup-card">
      <div className="feature-icon mb-3"><i className="bi bi-ticket-perforated" /></div>
      <h2>Olish kodini tekshirish</h2>
      <p className="muted">Tayyor buyurtmani topshirish uchun 6 xonali kodni kiriting.</p>
      <form onSubmit={submit}>
        <label className="field"><span>Olish kodi</span><input className="form-control pickup-code" name="code" inputMode="numeric" pattern="[0-9]{6}" maxLength="6" required /></label>
        <button className="btn btn-primary mt-2" type="submit">Tekshirish va topshirish</button>
      </form>
    </section>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [booting, setBooting] = useState(true);
  const [page, setPage] = useState("dashboard");
  const [orders, setOrders] = useState([]);
  const [prices, setPrices] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [notice, setNotice] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  function showNotice(message, tone = "info") {
    setNotice({ message, tone });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  useEffect(() => {
    getSession()
      .then((session) => setUser(session.user))
      .catch((error) => showNotice(error.message, "danger"))
      .finally(() => setBooting(false));
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    let active = true;
    const endpoint = {
      student: "/student/orders",
      operator: "/operator/orders",
      owner: "/owner/dashboard",
    }[user.role];
    if (!endpoint) return undefined;

    api(endpoint)
      .then((data) => {
        if (!active) return;
        if (user.role === "owner") {
          setOrders(data.orders);
          setPrices(data.prices);
        } else {
          setOrders(data.orders);
        }
      })
      .catch((error) => {
        if (active) showNotice(error.message, "danger");
      });
    return () => { active = false; };
  }, [user, refreshKey]);

  async function openDetails(orderId) {
    try {
      const result = await api(`/student/orders/${orderId}`);
      setSelectedOrder(result.order);
    } catch (error) {
      showNotice(error.message, "danger");
    }
  }

  async function changeStatus(orderId, status) {
    try {
      await api(`/operator/orders/${orderId}/status`, {
        method: "PATCH",
        body: { status },
      });
      setRefreshKey((value) => value + 1);
      showNotice("Buyurtma holati yangilandi.", "success");
    } catch (error) {
      showNotice(error.message, "danger");
    }
  }

  async function signOut() {
    try {
      await api("/auth/logout", { method: "POST" });
      setUser(null);
      setOrders([]);
      setSelectedOrder(null);
      setPage("dashboard");
    } catch (error) {
      showNotice(error.message, "danger");
    }
  }

  if (booting) {
    return <div className="screen-loading"><span className="spinner-border text-primary" /> <span>Print navbati yuklanmoqda...</span></div>;
  }

  if (!user) {
    return (
      <main className="container app-shell">
        {notice && <div className={`alert alert-${notice.tone}`}>{notice.message}</div>}
        <AuthPanel onLogin={setUser} onNotice={showNotice} />
      </main>
    );
  }

  const title = {
    student: "Mening buyurtmalarim",
    operator: "Operator navbati",
    owner: "Markaz boshqaruvi",
  }[user.role] || "Boshqaruv";

  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" onClick={(event) => { event.preventDefault(); setPage("dashboard"); setSelectedOrder(null); }}>
          <span className="brand-mark"><i className="bi bi-printer-fill" /></span>
          <span>Print navbati<small>Raqamli chop etish xizmati</small></span>
        </a>
        <nav className="main-nav">
          <button className={page === "dashboard" ? "active" : ""} onClick={() => { setPage("dashboard"); setSelectedOrder(null); }}>
            <i className="bi bi-grid-1x2" /> Bosh sahifa
          </button>
          {user.role === "student" && <button className={page === "new-order" ? "active" : ""} onClick={() => { setPage("new-order"); setSelectedOrder(null); }}><i className="bi bi-plus-circle" /> Yangi buyurtma</button>}
          {user.role === "operator" && <button className={page === "pickup" ? "active" : ""} onClick={() => setPage("pickup")}><i className="bi bi-ticket-perforated" /> Olish kodi</button>}
          {user.role === "owner" && <button className={page === "prices" ? "active" : ""} onClick={() => setPage("prices")}><i className="bi bi-sliders" /> Narxlar</button>}
        </nav>
        <div className="user-menu">
          <span className="avatar">{user.fullName.slice(0, 1).toUpperCase()}</span>
          <span className="user-label"><strong>{user.fullName}</strong><small>{user.role}</small></span>
          <button aria-label="Tizimdan chiqish" className="icon-button" onClick={signOut}><i className="bi bi-box-arrow-right" /></button>
        </div>
      </header>

      <main className="container app-main">
        {notice && <div className={`alert alert-${notice.tone} notice`}>{notice.message}<button aria-label="Yopish" onClick={() => setNotice(null)}>×</button></div>}
        {page === "new-order" && user.role === "student" && (
          <NewOrder
            onCreated={(result) => {
              setRefreshKey((value) => value + 1);
              showNotice(`Buyurtma ${result.order.number} yaratildi. Olish kodi: ${result.pickupCode}`, "success");
              setPage("dashboard");
            }}
            onNotice={showNotice}
          />
        )}
        {page === "prices" && user.role === "owner" && prices && (
          <PriceSettings prices={prices} onSave={setPrices} onNotice={showNotice} />
        )}
        {page === "pickup" && user.role === "operator" && (
          <PickupForm
            onNotice={showNotice}
            onComplete={() => setRefreshKey((value) => value + 1)}
          />
        )}
        {page === "dashboard" && selectedOrder && (
          <section className="detail-card panel">
            <button className="btn btn-sm btn-outline-secondary mb-3" onClick={() => setSelectedOrder(null)}>
              <i className="bi bi-arrow-left me-1" /> Buyurtmalarga qaytish
            </button>
            <div className="eyebrow text-primary">Buyurtma tafsilotlari</div>
            <h2>{selectedOrder.number}</h2>
            <p>Holat: <span className={`status-pill status-${selectedOrder.status}`}>{statusNames[selectedOrder.status]}</span></p>
            <p>Jami: <strong>{money(selectedOrder.totalPrice)}</strong></p>
            {selectedOrder.print && <p>{selectedOrder.print.pageFrom}–{selectedOrder.print.pageTo} bet · {selectedOrder.print.copies} nusxa · {selectedOrder.print.colorMode === "bw" ? "Oq-qora" : "Rangli"}</p>}
            {["new", "queued"].includes(selectedOrder.status) && (
              <button
                className="btn btn-outline-danger"
                onClick={async () => {
                  try {
                    await api(`/student/orders/${selectedOrder.id}/cancel`, { method: "POST" });
                    setSelectedOrder(null);
                    setRefreshKey((value) => value + 1);
                    showNotice("Buyurtma bekor qilindi.", "success");
                  } catch (error) {
                    showNotice(error.message, "danger");
                  }
                }}
              >
                Buyurtmani bekor qilish
              </button>
            )}
          </section>
        )}
        {page === "dashboard" && !selectedOrder && (
          <>
            <section className="dashboard-heading">
              <div>
                <div className="eyebrow text-primary">{new Date().toLocaleDateString("uz-UZ", { weekday: "long", day: "numeric", month: "long" })}</div>
                <h1>{title}</h1>
                <p className="muted">
                  {user.role === "student" && "Buyurtmalaringizni kuzating yoki yangi chop etish buyurtmasini yarating."}
                  {user.role === "operator" && "Yangi ishlarni navbat bo‘yicha boshqaring."}
                  {user.role === "owner" && "Markaz buyurtmalari va xizmat sozlamalarini boshqaring."}
                </p>
              </div>
              {user.role === "student" && <button className="btn btn-primary" onClick={() => setPage("new-order")}><i className="bi bi-plus-lg me-2" />Yangi buyurtma</button>}
            </section>
            <section className="summary-grid">
              <article className="stat-card"><span className="stat-icon"><i className="bi bi-files" /></span><span className="muted">Buyurtmalar</span><strong className="number">{orders.length}</strong></article>
              <article className="stat-card"><span className="stat-icon green"><i className="bi bi-check2-circle" /></span><span className="muted">Tayyor / topshirilgan</span><strong className="number">{orders.filter((order) => ["ready", "completed"].includes(order.status)).length}</strong></article>
              <article className="stat-card"><span className="stat-icon amber"><i className="bi bi-hourglass-split" /></span><span className="muted">Jarayonda</span><strong className="number">{orders.filter((order) => ["new", "queued", "printing"].includes(order.status)).length}</strong></article>
            </section>
            <section className="orders-section">
              <div className="section-heading"><div><h2>{user.role === "operator" ? "Faol navbat" : "So‘nggi buyurtmalar"}</h2><p className="muted">Buyurtma holati va tafsilotlari</p></div>
                {user.role === "owner" && <button className="btn btn-outline-primary" onClick={() => setPage("prices")}><i className="bi bi-sliders me-2" />Narxlarni sozlash</button>}
              </div>
              <OrderTable orders={orders} user={user} onDetails={openDetails} onStatusChange={changeStatus} />
            </section>
          </>
        )}
      </main>
      <footer className="app-footer">Print navbati <span>·</span> Nusxa ko‘paytirish markazi uchun raqamli navbat tizimi</footer>
    </div>
  );
}
