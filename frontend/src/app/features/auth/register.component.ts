import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <main class="auth-page">
      <form [formGroup]="form" (ngSubmit)="submit()" class="auth-card">
        <h1>Create account</h1>

        <label>
          <span>Username</span>
          <input formControlName="username" placeholder="Choose a username" autocomplete="username">
        </label>

        <label>
          <span>Email address</span>
          <input type="email" formControlName="email" placeholder="you@example.com" autocomplete="email">
        </label>

        <label>
          <span>Password</span>
          <input type="password" formControlName="password" placeholder="At least 8 characters" autocomplete="new-password">
        </label>

        <button type="submit" [disabled]="form.invalid || loading()">
          {{ loading() ? 'Creating...' : 'Create account' }}
        </button>

        <p class="error" *ngIf="error()">{{ error() }}</p>
        <p class="signup-link">Already have an account? <a routerLink="/login">Sign in</a></p>
      </form>
    </main>`,
  styles: [`
    .auth-card label { display: grid; gap: 7px; color: #cbd5e1; font-size: .82rem; font-weight: 650; }
    .signup-link { margin: 4px 0 0; color: #9baac2; text-align: center; }
  `]
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly form = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(150)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8), Validators.maxLength(128)]]
  });

  submit() {
    this.loading.set(true);
    this.error.set('');

    this.auth.register(
      this.form.value.username!,
      this.form.value.email!,
      this.form.value.password!
    ).subscribe({
      next: () => void this.router.navigate(['/login'], { queryParams: { registered: 'true' } }),
      error: error => {
        this.error.set(this.getErrorMessage(error));
        this.loading.set(false);
      },
      complete: () => this.loading.set(false)
    });
  }

  private getErrorMessage(error: unknown): string {
    const response = error as { status?: number; error?: { detail?: unknown } };
    const detail = response.error?.detail;

    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map(item => {
          if (typeof item === 'object' && item !== null && 'msg' in item) {
            const message = (item as { msg?: unknown }).msg;
            return typeof message === 'string'
              ? message.replace(/^Value error,?\s*/i, '')
              : '';
          }
          return '';
        })
        .filter(Boolean);
      if (messages.length) return messages.join(' ');
    }

    if (response.status === 409) return 'Username or email already exists.';
    if (response.status === 422) return 'Please check the username, email, and password fields.';
    return 'Unable to create account. Check that the backend is running and try again.';
  }
}
