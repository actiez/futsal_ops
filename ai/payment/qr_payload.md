# QR Payload Design (PayNow)

## Purpose
Generate QR codes that allow players to scan and pay with:
- amount pre-filled
- payee mobile number
- transaction reference

## Required Fields

- payee_mobile
- amount
- transaction_reference
- currency (SGD)

## Rules

- Each player must receive a unique QR
- Reference must match payment record
- Amount must match calculated amount
- QR must be generated after event completion