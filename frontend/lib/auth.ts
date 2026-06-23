"use client";

import { create } from "zustand";
import api from "./api";

interface User {
  id: string;
  email: string;
  full_name: string;
  is_verified: boolean;
}

interface Workspace {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  profile: Record<string, unknown>;
  created_at: string;
}

interface AuthState {
  user: User | null;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  fetchMe: () => Promise<void>;
  fetchWorkspaces: () => Promise<void>;
  setActiveWorkspace: (w: Workspace) => void;
}

const DEMO_USER = { id: "demo", email: "imvabhishek@gmail.com", full_name: "V Abhishek", is_verified: true };
const DEMO_WS = { id: "demo-ws", name: "My Workspace", slug: "my-workspace", owner_id: "demo", profile: {}, created_at: new Date().toISOString() };

export const useAuthStore = create<AuthState>((set, get) => ({
  user: DEMO_USER,
  workspaces: [DEMO_WS],
  activeWorkspace: DEMO_WS,
  isLoading: false,

  login: async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    await get().fetchMe();
    await get().fetchWorkspaces();
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, workspaces: [], activeWorkspace: null });
  },

  register: async (email, password, fullName = "") => {
    const { data } = await api.post("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    await get().fetchMe();
  },

  fetchMe: async () => {
    const { data } = await api.get("/auth/me");
    set({ user: data });
  },

  fetchWorkspaces: async () => {
    const { data } = await api.get("/workspaces");
    const workspaces = data as Workspace[];
    set({ workspaces });
    if (workspaces.length > 0 && !get().activeWorkspace) {
      set({ activeWorkspace: workspaces[0] });
    }
  },

  setActiveWorkspace: (w) => set({ activeWorkspace: w }),
}));

export type { User, Workspace };
