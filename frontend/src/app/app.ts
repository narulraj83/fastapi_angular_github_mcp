import { Component } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  template: `
  <nav class="top-nav">
    <a class="brand" routerLink="/dashboard"><span class="brand-mark">G</span> RepoAssistant</a>
    <div><a routerLink="/dashboard">Dashboard</a><a routerLink="/chat">AI Chat</a></div>
  </nav>
  <router-outlet />`
})
export class App {}
