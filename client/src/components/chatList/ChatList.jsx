import { Link } from 'react-router-dom';
import './chatList.css';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

const ChatList = () => {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const menuRef = useRef(null);
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    clickX: 0,
    clickY: 0,
    x: 0,
    y: 0,
    chatId: null,
    chatTitle: ''
  });

  const { isPending, error, data } = useQuery({
    queryKey: ["userChats"],
    queryFn: () =>
      fetch(`${import.meta.env.VITE_API_URL}/api/userchats`, {
        credentials: "include",
      }).then((res) => res.json(),),
  });

  const deleteMutation = useMutation({
    mutationFn: (chatId) => {
      return fetch(`${import.meta.env.VITE_API_URL}/api/chats/${chatId}`, {
        method: "DELETE",
        credentials: "include",
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userChats"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ chatId, title }) => {
      return fetch(`${import.meta.env.VITE_API_URL}/api/chats/${chatId}`, {
        method: "PATCH",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userChats"] });
      setEditingId(null);
    },
  });

  const handleContextMenu = (e, chat) => {
    e.preventDefault();
    e.stopPropagation();
    const clickX = e.clientX;
    const clickY = e.clientY;
    setContextMenu({
      visible: true,
      clickX,
      clickY,
      x: clickX,
      y: clickY,
      chatId: chat._id,
      chatTitle: chat.title
    });
  };

  const closeContextMenu = () => {
    setContextMenu({
      visible: false,
      clickX: 0,
      clickY: 0,
      x: 0,
      y: 0,
      chatId: null,
      chatTitle: ''
    });
  };

  const handleDelete = (chatId) => {
    if (window.confirm('Are you sure you want to delete this chat?')) {
      deleteMutation.mutate(chatId);
    }
    closeContextMenu();
  };

  const handleEdit = (chatId, chatTitle) => {
    setEditingId(chatId);
    setEditTitle(chatTitle);
    closeContextMenu();
  };

  const handleSave = (chatId) => {
    if (editTitle.trim()) {
      updateMutation.mutate({ chatId, title: editTitle });
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditTitle('');
  };

  // Close context menu when clicking anywhere
  useEffect(() => {
    const handleClick = () => closeContextMenu();
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  // Position context menu near cursor and keep it inside viewport.
  useLayoutEffect(() => {
    if (!contextMenu.visible) return;
    if (!menuRef.current) return;

    const OFFSET = 6;
    const MARGIN = 8;

    const rect = menuRef.current.getBoundingClientRect();
    let nextX = contextMenu.clickX + OFFSET;
    let nextY = contextMenu.clickY + OFFSET;

    const maxX = window.innerWidth - rect.width - MARGIN;
    const maxY = window.innerHeight - rect.height - MARGIN;

    if (nextX > maxX) nextX = Math.max(MARGIN, maxX);
    if (nextY > maxY) nextY = Math.max(MARGIN, maxY);
    if (nextX < MARGIN) nextX = MARGIN;
    if (nextY < MARGIN) nextY = MARGIN;

    if (nextX !== contextMenu.x || nextY !== contextMenu.y) {
      setContextMenu((prev) => ({ ...prev, x: nextX, y: nextY }));
    }
  }, [contextMenu.visible, contextMenu.clickX, contextMenu.clickY, contextMenu.x, contextMenu.y]);

  // Close on scroll/resize (scroll capture catches scrolling inside the sidebar list)
  useEffect(() => {
    if (!contextMenu.visible) return;
    const close = () => closeContextMenu();
    window.addEventListener('resize', close);
    window.addEventListener('scroll', close, true);
    return () => {
      window.removeEventListener('resize', close);
      window.removeEventListener('scroll', close, true);
    };
  }, [contextMenu.visible]);

  return (
    <div className='chatList'>
      <span className='title'>DASHBOARD</span>
      <Link to="/dashboard">Create a new Chat</Link>
      <Link to="/">Explore CheerCloud</Link>
      <Link to="/">Contact</Link>
      <hr />

      <span className='title'>RECENT CHATS</span>
      <div className="list">
        {isPending ? "Loading..." : error ? "Something went wrong!" : data?.map((chat) => (
          <div 
            className="chatItem" 
            key={chat._id}
            onContextMenu={(e) => handleContextMenu(e, chat)}
          >
            {editingId === chat._id ? (
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave(chat._id);
                  if (e.key === 'Escape') handleCancel();
                }}
                onBlur={() => handleSave(chat._id)}
                autoFocus
                className="editInput"
              />
            ) : (
              <Link to={`/dashboard/chats/${chat._id}`}>{chat.title}</Link>
            )}
          </div>
        ))}
      </div>
      <hr />
      <div className="upgrade">
        <img src="/logo.png" alt="" />
        <div className="texts">
          <span>Upgrade to Pro</span>
          <span>Unlock all features</span>
        </div>
      </div>

      {/* Context Menu */}
      {contextMenu.visible &&
        createPortal(
          <div
            ref={menuRef}
            className="contextMenu"
            style={{
              position: 'fixed',
              top: contextMenu.y,
              left: contextMenu.x
            }}
          >
            <button onClick={() => handleEdit(contextMenu.chatId, contextMenu.chatTitle)}>
              ✎ Rename
            </button>
            <button onClick={() => handleDelete(contextMenu.chatId)} className="delete">
              🗑 Delete
            </button>
          </div>,
          document.body
        )}
    </div>
  )
}

export default ChatList