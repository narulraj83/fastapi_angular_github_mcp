import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';

interface Tokens { access_token: string; refresh_token: string; token_type: string }

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private readonly api = 'http://127.0.0.1:8000/api/v1';
  readonly isAuthenticated = signal(typeof window !== 'undefined' && !!window.localStorage.getItem('access_token'));

  register(username: string, email: string, password: string) {
    return this.http.post(`${this.api}/auth/register`, { username, email, password });
  }

  login(email: string, password: string) {
    return this.http.post<Tokens>(`${this.api}/auth/login`, { email, password }).pipe(
      tap(tokens => {
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('access_token', tokens.access_token);
          window.localStorage.setItem('refresh_token', tokens.refresh_token);
        }
        this.isAuthenticated.set(true);
      })
    );
  }

  logout() {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('access_token');
      window.localStorage.removeItem('refresh_token');
    }
    this.isAuthenticated.set(false);
  }

  me() {
    return this.http.get(`${this.api}/auth/me`);
  }
}
