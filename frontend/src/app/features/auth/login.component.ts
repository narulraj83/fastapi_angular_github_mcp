import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <main class="auth-page github-auth-page">
      <section class="signin-shell" aria-labelledby="signin-title">
        <div class="signin-brand">
          <a class="brand auth-brand" routerLink="/dashboard">
            <span class="brand-mark">G</span>
            RepoAssistant
          </a>
        </div>

        <div class="signin-card">
          <div class="github-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" role="img">
              <path d="M12 .7a12 12 0 0 0-3.79 23.38c.6.11.82-.26.82-.58v-2.24c-3.34.73-4.04-1.42-4.04-1.42-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.21.09 1.85 1.24 1.85 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.69.82.58A12 12 0 0 0 12 .7Z"/>
            </svg>
          </div>

          <span class="signin-kicker">Welcome to RepoAssistant</span>
          <h1 id="signin-title">Sign in with GitHub</h1>
          <p class="signin-copy">Connect your GitHub account to explore repositories, review pull requests, and chat with your codebase.</p>

          <button class="github-signin-button" type="button" (click)="signInWithGitHub()" [disabled]="githubLoading()">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 .7a12 12 0 0 0-3.79 23.38c.6.11.82-.26.82-.58v-2.24c-3.34.73-4.04-1.42-4.04-1.42-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.21.09 1.85 1.24 1.85 1.24 1.07 1.84 2.81 1.31 3.5 1 .11-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.69.82.58A12 12 0 0 0 12 .7Z"/>
            </svg>
            {{ githubLoading() ? 'Opening GitHub...' : 'Continue with GitHub' }}
          </button>

          <p class="oauth-error" *ngIf="githubError()">{{ githubError() }}</p>

          <div class="signin-divider"><span>or use your account</span></div>

          <form [formGroup]="form" (ngSubmit)="submit()" class="signin-form">
            <label>
              <span>Email address</span>
              <input type="email" formControlName="email" placeholder="you@example.com" autocomplete="email">
            </label>
            <label>
              <span>Password</span>
              <input type="password" formControlName="password" placeholder="Enter your password" autocomplete="current-password">
            </label>
            <button class="email-signin-button" [disabled]="form.invalid || loading()">
              {{ loading() ? 'Signing in...' : 'Sign in' }}
            </button>
          </form>

          <p class="error">{{ error() }}</p>
          <p class="signup-link">New to RepoAssistant? <a routerLink="/register">Create an account</a></p>
        </div>

        <p class="signin-footer">By continuing, you agree to the Terms of Service and Privacy Policy.</p>
      </section>
    </main>`,
  styles: [`
    :host { display: block; }
    .github-auth-page { min-height: 100vh; padding: 24px; background: radial-gradient(circle at 50% 10%, #17213a 0, #0b1020 44%, #080c16 100%); }
    .signin-shell { width: min(460px, 100%); display: flex; flex-direction: column; align-items: center; }
    .signin-brand { width: 100%; margin-bottom: 24px; }
    .auth-brand { display: inline-flex; align-items: center; }
    .signin-card { width: 100%; padding: 38px 40px 30px; border: 1px solid #26344d; border-radius: 18px; background: rgba(17, 24, 39, .96); box-shadow: 0 24px 70px rgba(0,0,0,.38); text-align: center; }
    .github-mark { width: 54px; height: 54px; display: grid; place-items: center; margin: 0 auto 18px; border: 1px solid #33415b; border-radius: 14px; background: #0b1020; }
    .github-mark svg { width: 30px; height: 30px; fill: #f7f9fc; }
    .signin-kicker { color: #22c55e; font-size: .72rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
    .signin-card h1 { margin: 8px 0 10px; color: #eef4ff; font-size: 1.75rem; }
    .signin-copy { margin: 0 auto 24px; color: #9baac2; line-height: 1.55; }
    .github-signin-button, .email-signin-button { width: 100%; height: 46px; border: 0; border-radius: 9px; font-weight: 700; }
    .github-signin-button { display: flex; align-items: center; justify-content: center; gap: 10px; background: #f2f5f9; color: #101827; }
    .github-signin-button svg { width: 20px; height: 20px; fill: #101827; }
    .github-signin-button:disabled { opacity: .65; }
    .oauth-error { margin: 12px 0 0; color: #fb7185; font-size: .88rem; }
    .signin-divider { display: flex; align-items: center; gap: 12px; margin: 22px 0; color: #7f8da5; font-size: .78rem; }
    .signin-divider::before, .signin-divider::after { content: ''; height: 1px; flex: 1; background: #26344d; }
    .signin-form { display: grid; gap: 12px; text-align: left; }
    .signin-form label { display: grid; gap: 7px; color: #cbd5e1; font-size: .82rem; font-weight: 650; }
    .signin-form input { height: 46px; }
    .email-signin-button { margin-top: 3px; background: #7c5cff; color: white; }
    .signup-link { margin: 18px 0 0; color: #9baac2; }
    .signin-footer { margin: 18px 0 0; color: #66748b; font-size: .75rem; text-align: center; }
    @media (max-width: 600px) { .github-auth-page { padding: 16px; } .signin-card { padding: 30px 22px 24px; } }
  `]
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  readonly loading = signal(false);
  readonly githubLoading = signal(false);
  readonly error = signal('');
  readonly githubError = signal('');
  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });

  signInWithGitHub() {
    if (typeof window === 'undefined') return;
    this.githubLoading.set(true);
    this.githubError.set('');
    this.http.get<{ authorization_url: string }>('http://127.0.0.1:8000/api/v1/github/signin').subscribe({
      next: data => window.location.assign(data.authorization_url),
      error: error => {
        this.githubLoading.set(false);
        this.githubError.set(error.error?.detail || 'Unable to start GitHub sign-in.');
      }
    });
  }

  submit() {
    this.loading.set(true);
    this.error.set('');
    this.auth.login(this.form.value.email!, this.form.value.password!).subscribe({
      next: () => void this.router.navigate(['/dashboard']),
      complete: () => this.loading.set(false),
      error: error => {
        this.error.set(error.error?.detail || 'Login failed');
        this.loading.set(false);
      }
    });
  }
}
