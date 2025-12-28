import express from "express"
import cors from "cors"
import ImageKit from "imagekit"
import mongoose from "mongoose";
import UserChats from "./models/userChats.js";
import Chat from "./models/chat.js";
import { requireAuth } from '@clerk/express'

const port = process.env.PORT || 3000;
const app = express();

app.use(
    cors({
        origin: process.env.CLIENT_URL,
        credentials: true,
    })
);

app.use(express.json());

let mongoConnected = false;

const connect = async () => {
    try {
        if (process.env.MONGO && process.env.MONGO !== 'your-mongodb-uri') {
            await mongoose.connect(process.env.MONGO);
            console.log("✅ Connected to MongoDB");
            mongoConnected = true;
        } else {
            console.log("⚠️  MongoDB not configured - running without database (chats won't be saved)");
            mongoConnected = false;
        }
    } catch (err) {
        console.log("⚠️  MongoDB connection failed:", err.message);
        console.log("⚠️  Running without database (chats won't be saved)");
        mongoConnected = false;
    }
}

const imagekit = new ImageKit({
    urlEndpoint: process.env.IMAGE_KIT_ENDPOINT,
    publicKey: process.env.IMAGE_KIT_PUBLIC_KEY,
    privateKey: process.env.IMAGE_KIT_PRIVATE_KEY
});

app.get("/api/upload", (req, res) => {
    const result = imagekit.getAuthenticationParameters();
    res.send(result);
});

// Test endpoint - no auth or database required
app.post("/api/test-chat", async (req, res) => {
    try {
        const { message } = req.body;
        res.json({ 
            success: true, 
            response: `AI received your message: "${message}". This is a test response. Please configure MongoDB and ImageKit for full functionality.`
        });
    } catch (err) {
        console.log(err);
        res.status(500).send("Error processing message");
    }
});

// app.get("/api/test", requireAuth(), (req, res) => {
//     const userId = req.auth.userId;
//     console.log(userId);
//     res.send("Success!")
// });

app.post("/api/chats",
    requireAuth(),
    async (req, res) => {

        const { text } = req.body;
        const userId = req.auth.userId;

        try {
            // CREATE A NEW CHAT
            const newChat = new Chat({
                userId: userId,
                history: [{ role: "user", parts: [{ text }] }],
            });

            const savedChat = await newChat.save();

            // CHECK IF THE USERCHATS EXIST
            const userChats = await UserChats.find({ userId: userId });

            // IF NOT EXIST CREATE NEW THEN ADD TO ARR
            if (!userChats.length) {
                const newUserChats = new UserChats({
                    userId: userId,
                    chats: [
                        {
                            _id: savedChat._id,
                            title: text.substring(0, 40),
                        },
                    ],
                });

                await newUserChats.save();
                res.status(201).send(savedChat._id);
            } else {
                // IF EXISTS, PUSH THE CHAT TO THE EXISTING ARRAY
                await UserChats.updateOne(
                    { userId: userId },
                    {
                        $push: {
                            chats: {
                                _id: savedChat._id,
                                title: text.substring(0, 40),
                            },
                        },
                    }
                );

                res.status(201).send(newChat._id);
            }
        } catch (err) {
            console.log(err);
            res.status(500).send("Error fetching userchats!")
        }
    });

app.get("/api/userchats", requireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        const userChats = await UserChats.find({ userId });

        if (!userChats.length) {
            res.status(200).send([]);
        } else {
            res.status(200).send(userChats[0].chats);
        }
    } catch (err) {
        console.log(err);
        res.status(500).send("Error fetching userchats!")
    }
})


app.get("/api/chats/:id", requireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        const chat = await Chat.findOne({ _id: req.params.id, userId });

        res.status(200).send(chat);
    } catch (err) {
        console.log(err);
        res.status(500).send("Error fetching chat!")
    }
});

app.put("/api/chats/:id", requireAuth(), async (req, res)=>{
    const userId = req.auth.userId;

    const {question, answer, img} = req.body;
    const newItems = [
        ...(question ? [{role: "user", parts: [{ text: question }], ... (img && { img })}] : []),
        { role: "model", parts: [{ text: answer }] },
    ];

    try {
        const updatedChat = await Chat.updateOne({_id: req.params.id, userId}, {
            $push: {
                history: {
                    $each: newItems,
                }
            }
        });
        res.status(200).send(updatedChat);
    } catch (err) {
        console.log(err)
        res.status(500).send("Error adding conversation!")
    }
})

app.delete("/api/chats/:id", requireAuth(), async (req, res) => {
    const userId = req.auth.userId;

    try {
        // Delete the chat
        await Chat.deleteOne({ _id: req.params.id, userId });
        
        // Remove from user's chat list
        await UserChats.updateOne(
            { userId: userId },
            { $pull: { chats: { _id: req.params.id } } }
        );

        res.status(200).send("Chat deleted successfully!");
    } catch (err) {
        console.log(err);
        res.status(500).send("Error deleting chat!");
    }
});

app.patch("/api/chats/:id", requireAuth(), async (req, res) => {
    const userId = req.auth.userId;
    const { title } = req.body;

    try {
        // Update the chat title in Chat collection
        await Chat.updateOne(
            { _id: req.params.id, userId },
            { $set: { title: title } }
        );

        // Update the title in UserChats collection
        await UserChats.updateOne(
            { userId: userId, "chats._id": req.params.id },
            { $set: { "chats.$.title": title } }
        );

        res.status(200).send("Chat title updated successfully!");
    } catch (err) {
        console.log(err);
        res.status(500).send("Error updating chat title!");
    }
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(401).send("Unauthenticated!");
});

app.listen(port, () => {
    connect();
    console.log("Server running on 3000")
});