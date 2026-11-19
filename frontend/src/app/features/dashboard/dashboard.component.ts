import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { RepositoryService, Repository } from '../../core/services/repository.service';

@Component({ standalone: true, imports: [CommonModule, RouterLink], template: `
<div class="dashboard"><header><div><span class="eyebrow">WORKSPACE</span><h1>Repository Assistant</h1></div><button (click)="connectGitHub()" [disabled]="githubLoading()">{{ githubLoading() ? 'Connecting...' : 'Connect GitHub' }}</button></header>
<p class="error" *ngIf="githubError()">{{ githubError() }}</p>
<section class="stats"><article><span>Repositories</span><strong>{{ repositories().length }}</strong></article><article><span>Chat sessions</span><strong>—</strong></article><article><span>Analysis reports</span><strong>—</strong></article><article><span>Pull requests</span><strong>—</strong></article></section>
<section><div class="section-title"><h2>Your repositories</h2></div><div class="repo-grid"><article *ngFor="let repo of repositories()" class="repo-card"><span class="visibility">{{ repo.visibility }}</span><h3>{{ repo.full_name }}</h3><p>{{ repo.description || 'No description' }}</p><div><span>{{ repo.default_branch }}</span><a [routerLink]="['/repositories', repo.id]">Open</a></div></article></div></section>
</div>` })
export class DashboardComponent {
  private readonly repositoriesService = inject(RepositoryService);
  private readonly http = inject(HttpClient);
  readonly repositories = signal<Repository[]>([]);
  readonly githubLoading = signal(false);
  readonly githubError = signal('');

  constructor() {
    this.refreshRepositories();
  }

  private refreshRepositories() {
    if (typeof window === 'undefined') return;

    this.http.post<{ synced: number }>('http://127.0.0.1:8000/api/v1/github/sync', {}).subscribe({
      next: () => this.loadRepositories(),
      error: () => this.loadRepositories()
    });
  }

  private loadRepositories() {
    this.repositoriesService.list().subscribe({
      next: data => this.repositories.set(data),
      error: error => this.githubError.set(error.error?.detail || 'Unable to load repositories.')
    });
  }

  connectGitHub() {
    if (typeof window === 'undefined') return;

    const token = window.localStorage.getItem('access_token');
    if (!token) {
      this.githubError.set('Please sign in before connecting GitHub.');
      return;
    }

    this.githubLoading.set(true);
    this.githubError.set('');
    this.http.get<{ authorization_url: string }>('http://127.0.0.1:8000/api/v1/github/connect').subscribe({
      next: data => {
        window.location.assign(data.authorization_url);
      },
      error: error => {
        this.githubLoading.set(false);
        this.githubError.set(error.error?.detail || 'Unable to start GitHub authorization.');
      }
    });
  }
}
