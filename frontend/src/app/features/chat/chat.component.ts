import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ChatService } from '../../core/services/chat.service';
import { RepositoryService, Repository } from '../../core/services/repository.service';

@Component({ standalone: true, imports: [CommonModule, FormsModule], template: `
<div class="chat-page">
  <aside>
    <h2>Conversations</h2>
    <button (click)="newChat()" [disabled]="repositories().length === 0">+ New conversation</button>
    <p class="error" *ngIf="error()">{{ error() }}</p>

    <label class="chat-repository" *ngIf="repositories().length">
      <span>Repository</span>
      <select [(ngModel)]="repositoryId" name="repositoryId" (change)="selectRepository()">
        <option [ngValue]="null">Select repository</option>
        <option *ngFor="let repository of repositories()" [ngValue]="repository.id">{{ repository.full_name }}</option>
      </select>
    </label>

    <button *ngFor="let session of sessions()" (click)="openSession(session.id)">{{ session.session_title }}</button>
  </aside>

  <main>
    <div class="messages">
      <article *ngFor="let message of messages()" [class.user]="message.role === 'user'">
        <strong>{{ message.role }}</strong><p>{{ message.message }}</p>
      </article>
      <p *ngIf="sending()">Assistant is thinking...</p>
    </div>

    <form (ngSubmit)="send()" class="composer">
      <input [(ngModel)]="question" name="question" placeholder="Ask about this repository..." [disabled]="!sessionId() || sending()">
      <button [disabled]="!question.trim() || !sessionId() || sending()">Send</button>
    </form>
  </main>
</div>`, styles: [`
  .chat-repository { display: grid; gap: 6px; margin: 12px 0; }
  .chat-repository span { color: #9baac2; font-size: .8rem; }
  .chat-repository select { width: 100%; padding: 9px; border: 1px solid #26344d; border-radius: 7px; background: #0c1322; color: white; }
`] })
export class ChatComponent {
  private readonly chat = inject(ChatService);
  private readonly repositoriesService = inject(RepositoryService);
  private readonly route = inject(ActivatedRoute);

  readonly sessions = signal<any[]>([]);
  readonly repositories = signal<Repository[]>([]);
  readonly messages = signal<any[]>([]);
  readonly sessionId = signal<number | null>(null);
  readonly sending = signal(false);
  readonly error = signal('');
  repositoryId: number | null = null;
  question = '';

  constructor() {
    this.chat.listSessions().subscribe({
      next: data => this.sessions.set(data),
      error: error => this.error.set(error.error?.detail || 'Unable to load conversations.')
    });

    this.repositoriesService.list().subscribe({
      next: data => {
        this.repositories.set(data);
        const routeId = Number(this.route.snapshot.queryParamMap.get('repositoryId'));
        const selected = routeId || (data.length ? data[0].id : null);
        if (selected) {
          this.repositoryId = selected;
          this.findOrCreateSession(selected);
        }
      },
      error: error => this.error.set(error.error?.detail || 'Unable to load repositories.')
    });
  }

  selectRepository() {
    if (this.repositoryId) this.findOrCreateSession(this.repositoryId);
  }

  private findOrCreateSession(repositoryId: number) {
    const existing = this.sessions().find(session => session.repository_id === repositoryId);
    if (existing) {
      this.openSession(existing.id);
      return;
    }
    this.newChat();
  }

  newChat() {
    if (!this.repositoryId) {
      this.error.set('Select a repository first.');
      return;
    }

    this.error.set('');
    this.chat.createSession(this.repositoryId).subscribe({
      next: session => {
        this.sessionId.set(session.id);
        this.messages.set([]);
        this.sessions.update(items => [session, ...items]);
      },
      error: error => this.error.set(error.error?.detail || 'Unable to create a conversation.')
    });
  }

  openSession(id: number) {
    this.sessionId.set(id);
    this.error.set('');
    this.chat.getSession(id).subscribe({
      next: data => this.messages.set(data.messages || []),
      error: error => this.error.set(error.error?.detail || 'Unable to open conversation.')
    });
  }

  send() {
    const id = this.sessionId();
    if (!id || !this.question.trim() || this.sending()) return;

    const question = this.question.trim();
    this.question = '';
    this.sending.set(true);
    this.error.set('');
    this.messages.update(items => [...items, { role: 'user', message: question }]);

    this.chat.sendMessage(id, question).subscribe({
      next: message => this.messages.update(items => [...items, message]),
      error: error => {
        this.error.set(error.error?.detail || 'Unable to send message.');
        this.sending.set(false);
      },
      complete: () => this.sending.set(false)
    });
  }
}
