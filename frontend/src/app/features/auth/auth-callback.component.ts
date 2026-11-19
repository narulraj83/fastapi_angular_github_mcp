import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  standalone: true,
  template: `<main class="auth-page"><section class="auth-card"><h1>Completing GitHub sign-in...</h1></section></main>`
})
export class AuthCallbackComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);

  ngOnInit(): void {
    if (typeof window === 'undefined') return;

    const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (!accessToken || !refreshToken) {
      void this.router.navigate(['/login'], { queryParams: { error: 'github_signin_failed' } });
      return;
    }

    window.localStorage.setItem('access_token', accessToken);
    window.localStorage.setItem('refresh_token', refreshToken);
    this.auth.isAuthenticated.set(true);
    window.history.replaceState({}, document.title, '/dashboard');
    void this.router.navigate(['/dashboard']);
  }
}
